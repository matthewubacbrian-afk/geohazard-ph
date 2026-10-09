import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../src/components/map/MapView', () => ({
  default: () => <div aria-label="Hazard map" />,
}));

vi.mock('../src/hooks/useEventSummary', () => ({
  useEventSummary: vi.fn(),
}));

vi.mock('../src/hooks/useRiskProfiles', () => ({
  useRiskProfiles: vi.fn(() => ({ data: [], error: null, refetch: vi.fn() })),
}));

import DashboardMapArea from '../src/components/dashboard/DashboardMapArea';
import { useEventSummary } from '../src/hooks/useEventSummary';
import { useRiskProfiles } from '../src/hooks/useRiskProfiles';

const mockedUseEventSummary = vi.mocked(useEventSummary);
const mockedUseRiskProfiles = vi.mocked(useRiskProfiles);

function renderSummary() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <DashboardMapArea events={[]} isLoading={false} error={null} onRetry={vi.fn()} />
    </QueryClientProvider>,
  );
}

describe('Dashboard summary states', () => {
  it('uses canonical risk labels and describes the unfiltered area count', () => {
    mockedUseEventSummary.mockReturnValue({
      data: { event_count: 12, avg_magnitude: 4.5 },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as never);
    mockedUseRiskProfiles.mockReturnValue({ data: [], error: null, refetch: vi.fn() } as never);

    renderSummary();

    expect(screen.getByText('Regional risk profile')).toBeInTheDocument();
    for (const label of ['Low', 'Moderate', 'High', 'Very High']) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    expect(screen.queryByText(/PGA|Critical|Elevated|Baseline/)).not.toBeInTheDocument();
    expect(screen.getByText('Events in area')).toBeInTheDocument();
    expect(screen.getByText('4.50')).toBeInTheDocument();
    expect(screen.getByText('12', { exact: true })).toBeInTheDocument();
    expect(screen.getAllByText('Coming soon')).toHaveLength(2);
    expect(screen.queryByText('Frequency (YTD)')).not.toBeInTheDocument();
  });
  it('shows a retry action when the summary request fails', () => {
    const refetch = vi.fn();
    mockedUseEventSummary.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('summary unavailable'),
      refetch,
    } as never);

    renderSummary();

    expect(screen.getByText(/summary unavailable/i)).toBeInTheDocument();
    screen.getByRole('button', { name: /retry summary/i }).click();
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it('shows an empty state when the summary has no data', () => {
    mockedUseEventSummary.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as never);

    renderSummary();

    expect(screen.getByText(/no regional summary available/i)).toBeInTheDocument();
  });

  it('shows a retry action when the risk overlay request fails', () => {
    const refetch = vi.fn();
    mockedUseRiskProfiles.mockReturnValue({
      data: [],
      error: new Error('risk unavailable'),
      refetch,
    } as never);

    renderSummary();

    expect(screen.getByText(/risk overlay unavailable/i)).toBeInTheDocument();
    screen.getByRole('button', { name: /retry risk overlay/i }).click();
    expect(refetch).toHaveBeenCalledTimes(1);
  });
});
