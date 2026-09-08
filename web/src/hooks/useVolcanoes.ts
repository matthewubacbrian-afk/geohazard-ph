import { useQuery } from '@tanstack/react-query';
import { fetchVolcanoes } from '../api/volcanoes';

export function useVolcanoes() {
  return useQuery({
    queryKey: ['volcanoes'],
    queryFn: ({ signal }) => fetchVolcanoes(signal),
    staleTime: 60000,
    refetchInterval: 60000,
    retry: false,
  });
}
