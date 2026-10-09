import { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { applyEventChange, parseEventChange, realtimeUrl } from '../api/realtime';
import type { HazardEvent } from '../types/hazard';

export function useRealtimeAlerts() {
  const client = useQueryClient();
  const [connected, setConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  useEffect(() => {
    let stopped = false;
    let socket: WebSocket | null = null;
    let retry: ReturnType<typeof setTimeout> | undefined;
    let watchdog: ReturnType<typeof setTimeout> | undefined;
    let attempt = 0;
    let pending = Promise.resolve();

    function reconnect() {
      if (stopped) return;
      setConnected(false);
      clearTimeout(watchdog);
      const delay = Math.min(30000, 1000 * 2 ** Math.min(attempt++, 5));
      retry = setTimeout(connect, delay + Math.random() * delay * 0.2);
    }
    function connect() {
      if (stopped) return;
      try {
        socket = new WebSocket(realtimeUrl());
      } catch {
        reconnect();
        return;
      }
      const current = socket;
      watchdog = setTimeout(() => current.close(), 10000);
      current.onopen = () => {
        if (stopped) return;
        clearTimeout(watchdog);
        attempt = 0;
        setConnected(true);
        // Redis pub/sub has no replay. Reconcile both initial handshake and reconnect gaps.
        void client.invalidateQueries({ queryKey: ['events'] });
        void client.invalidateQueries({ queryKey: ['event-summary'] });
      };
      current.onmessage = ({ data }) => {
        if (stopped) return;
        try {
          const change = parseEventChange(data);
          pending = pending.then(async () => {
            await client.cancelQueries({ queryKey: ['events'] });
            if (stopped) return;
            const cached = client.getQueriesData<HazardEvent[]>({ queryKey: ['events'] });
            for (const [queryKey, previous] of cached) {
              if (!previous) continue;
              const options = queryKey[1];
              const since = options && typeof options === 'object' && 'since' in options &&
                typeof options.since === 'string' ? Date.parse(options.since) : null;
              const updated = applyEventChange(previous, change);
              client.setQueryData(queryKey, since === null
                ? updated
                : updated.filter((event) => Date.parse(event.occurred_at) >= since));
            }
            // A push cannot fill a query that has not loaded its initial snapshot.
            if (cached.some(([, previous]) => previous === undefined) || cached.length === 0) {
              void client.invalidateQueries({
                queryKey: ['events'],
                predicate: (query) => query.state.data === undefined,
              });
            }
            setLastUpdated(new Date().toISOString());
            void client.invalidateQueries({ queryKey: ['event-summary'] });
          }).catch(() => current.close(1011, 'Unable to apply event'));
        } catch {
          // Explicitly reconnect/refetch on invalid data; never poison the query cache.
          current.close(1003, 'Invalid event');
        }
      };
      current.onerror = () => current.close();
      current.onclose = reconnect;
    }
    connect();
    return () => {
      stopped = true;
      clearTimeout(retry);
      clearTimeout(watchdog);
      if (socket) {
        socket.onopen = null;
        socket.onmessage = null;
        socket.onclose = null;
        socket.onerror = null;
        socket.close();
      }
    };
  }, [client]);

  return { connected, lastUpdated };
}
