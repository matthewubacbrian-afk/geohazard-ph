import { useQuery } from '@tanstack/react-query';

import { fetchEventSummary } from '../api/client';

export function useEventSummary() {
  return useQuery({
    queryKey: ['event-summary'],
    queryFn: () => fetchEventSummary(),
  });
}
