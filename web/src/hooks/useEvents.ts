import { useQuery } from '@tanstack/react-query';

import { fetchEvents } from '../api/client';

export function useEvents(source = '') {
  return useQuery({
    queryKey: ['events'],
    queryFn: ({ signal }) => fetchEvents(signal),
    select: (events) => events.filter((event) =>
      event.is_primary !== false && (!source || event.source === source)),
    refetchInterval: 30000,
  });
}
