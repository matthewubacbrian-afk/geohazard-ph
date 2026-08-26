import { useQuery } from '@tanstack/react-query';
import { fetchRiskProfiles } from '../api/client';

export function useRiskProfiles() {
  return useQuery({
    queryKey: ['risk-profiles'],
    queryFn: fetchRiskProfiles,
  });
}
