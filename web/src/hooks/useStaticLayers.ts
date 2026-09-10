import { useQuery } from '@tanstack/react-query';
import { fetchStaticLayers } from '../api/staticLayers';
import type { StaticLayerKind } from '../types/staticLayer';

export function useStaticLayers(kind: StaticLayerKind, enabled: boolean) {
  return useQuery({
    queryKey: ['static-layers', kind],
    queryFn: ({ signal }) => fetchStaticLayers(kind, signal),
    enabled,
    staleTime: 60 * 60 * 1000,
  });
}
