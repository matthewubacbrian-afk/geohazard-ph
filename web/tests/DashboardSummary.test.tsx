import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../src/components/map/MapView', () => ({
  default: () => <div aria-label="Hazard map" />,
}));

vi.mock('../src/hooks/useRiskProfiles', () => ({
  useRiskProfiles: vi.fn(() => ({ data: [], error: null, refetch: vi.fn() })),
}));

import DashboardMapArea from '../src/components/dashboard/DashboardMapArea';
import { useRiskProfiles } from '../src/hooks/useRiskProfiles';

const mockedUseRiskProfiles = vi.mocked(useRiskProfiles);

function renderMapArea() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <DashboardMapArea events={[]} isLoading={false} error={null} onRetry={vi.fn()} />
    </QueryClientProvider>,
  );
}

describe('Dashboard map overlays', () => {
  it('uses canonical risk labels', () => {
    mockedUseRiskProfiles.mockReturnValue({ data: [], error: null, refetch: vi.fn() } as never);
    renderMapArea();

    expect(screen.getByText('Regional risk profile')).toBeInTheDocument();
    for (const label of ['Low', 'Moderate', 'High', 'Very High']) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    expect(screen.queryByText(/PGA|Critical|Elevated|Baseline/)).not.toBeInTheDocument();
  });

  it('shows a retry action when the risk overlay request fails', () => {
    const refetch = vi.fn();
    mockedUseRiskProfiles.mockReturnValue({
      data: [],
      error: new Error('risk unavailable'),
      refetch,
    } as never);
    renderMapArea();

    expect(screen.getByText(/risk overlay unavailable/i)).toBeInTheDocument();
    screen.getByRole('button', { name: /retry risk overlay/i }).click();
    expect(refetch).toHaveBeenCalledTimes(1);
  });
});
