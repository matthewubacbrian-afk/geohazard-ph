import { useQuery } from '@tanstack/react-query';

import { fetchEvents, type EventQueryParams } from '../api/client';

export type EventFilters = EventQueryParams & {
  until?: string;
  minMagnitude?: number;
  maxMagnitude?: number;
};

export function useEvents(input: EventFilters | string = {}) {
  const filters: EventFilters = typeof input === 'string' ? { source: input } : input;

  return useQuery({
    queryKey: filters.since ? ['events', { since: filters.since }] : ['events'],
    queryFn: ({ signal }) => fetchEvents(
      filters.since ? { since: filters.since } : undefined,
      signal,
    ),
    select: (events) => events.filter((event) =>
      event.is_primary !== false &&
      (!filters.source || event.source === filters.source) &&
      (filters.until === undefined || event.occurred_at <= filters.until) &&
      (filters.minMagnitude === undefined ||
        (event.magnitude ?? Number.NEGATIVE_INFINITY) >= filters.minMagnitude) &&
      (filters.maxMagnitude === undefined ||
        (event.magnitude ?? Number.POSITIVE_INFINITY) <= filters.maxMagnitude)),
    refetchInterval: 30000,
  });
}
