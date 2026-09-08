import { act, cleanup, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { useRealtimeAlerts } from '../src/hooks/useRealtimeAlerts';
import { applyEventChange } from '../src/api/realtime';
import type { EventChange } from '../src/types/hazard';

const event: EventChange = {
  id: '00000000-0000-4000-8000-000000000001',
  canonical_id: '00000000-0000-4000-8000-000000000003', is_primary: true,
  source: 'usgs', hazard_type: 'earthquake', external_id: 'us1',
  latitude: 15, longitude: 121, magnitude: 5, depth_km: 10,
  occurred_at: '2026-08-29T09:30:00Z', place_name: 'Sample',
};
class Socket {
  static instances: Socket[] = [];
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  close = vi.fn(() => this.onclose?.());
  constructor() { Socket.instances.push(this); }
}
function Status() {
  const state = useRealtimeAlerts();
  return <div>{state.connected ? 'LIVE' : 'Reconnecting'}</div>;
}
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.useRealTimers(); Socket.instances = []; });

describe('realtime events', () => {
  it('replaces canonical markers in either demotion arrival order and is idempotent', () => {
    const primary = { ...event, id: '00000000-0000-4000-8000-000000000002', source: 'phivolcs' };
    const demoted = { ...event, is_primary: false };
    expect(applyEventChange(applyEventChange([event], primary), demoted)).toEqual([primary]);
    expect(applyEventChange(applyEventChange([event], demoted), primary)).toEqual([primary]);
    expect(applyEventChange([primary], primary)).toEqual([primary]);
  });
  it('connects, updates the shared cache, reconnects and cleans up', async () => {
    vi.useFakeTimers();
    vi.stubGlobal('WebSocket', Socket);
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    client.setQueryData(['events'], [event]);
    const view = render(<QueryClientProvider client={client}><Status /></QueryClientProvider>);
    const socket = Socket.instances[0];
    act(() => socket.onopen?.());
    expect(screen.getByText('LIVE')).toBeTruthy();
    await act(async () => socket.onmessage?.({ data: JSON.stringify({ ...event, magnitude: 6 }) }));
    expect(client.getQueryData<EventChange[]>(['events'])?.[0].magnitude).toBe(6);
    act(() => socket.onclose?.());
    expect(screen.getByText('Reconnecting')).toBeTruthy();
    act(() => vi.advanceTimersByTime(1500));
    expect(Socket.instances).toHaveLength(2);
    view.unmount();
    expect(Socket.instances[1].close).toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(60000));
    expect(Socket.instances).toHaveLength(2);
  });
  it('rejects malformed data and refetches after reconnection', () => {
    vi.useFakeTimers();
    vi.stubGlobal('WebSocket', Socket);
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, 'invalidateQueries');
    render(<QueryClientProvider client={client}><Status /></QueryClientProvider>);
    act(() => Socket.instances[0].onopen?.());
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['events'] });
    act(() => Socket.instances[0].onmessage?.({ data: '{"id":"invalid"}' }));
    expect(Socket.instances[0].close).toHaveBeenCalled();
    expect(client.getQueryData(['events'])).toBeUndefined();
  });
});
