import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../src/hooks/useEventSummary', () => ({ useEventSummary: vi.fn() }));

import DashboardInfoPanel from '../src/components/dashboard/DashboardInfoPanel';
import { useEventSummary } from '../src/hooks/useEventSummary';

const mockedUseEventSummary = vi.mocked(useEventSummary);

describe('DashboardInfoPanel', () => {
  it('preserves API summary data, report navigation and the public information note', () => {
    const onViewDetailedReport = vi.fn();
    mockedUseEventSummary.mockReturnValue({
      data: { event_count: 12, avg_magnitude: 4.5 },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as never);

    render(<DashboardInfoPanel onViewDetailedReport={onViewDetailedReport} />);

    expect(screen.getByText('12', { exact: true })).toBeInTheDocument();
    expect(screen.getByText('4.50')).toBeInTheDocument();
    expect(screen.getByText(/not an official PHIVOLCS\/NDRRMC warning or forecast/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'View Detailed Report' }));
    expect(onViewDetailedReport).toHaveBeenCalledTimes(1);
  });

  it('keeps loading, retryable error and empty summary states available', () => {
    const refetch = vi.fn();
    mockedUseEventSummary.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch,
    } as never);
    const { rerender } = render(<DashboardInfoPanel onViewDetailedReport={vi.fn()} />);
    expect(screen.getByRole('status', { name: 'Loading event summary' })).toBeInTheDocument();

    mockedUseEventSummary.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('summary unavailable'),
      refetch,
    } as never);
    rerender(<DashboardInfoPanel onViewDetailedReport={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /retry summary/i }));
    expect(refetch).toHaveBeenCalledTimes(1);

    mockedUseEventSummary.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
      refetch,
    } as never);
    rerender(<DashboardInfoPanel onViewDetailedReport={vi.fn()} />);
    expect(screen.getByText(/no regional summary available/i)).toBeInTheDocument();
  });

  it('can be closed without affecting other dashboard controls', () => {
    mockedUseEventSummary.mockReturnValue({
      data: { event_count: 1 },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as never);
    render(<DashboardInfoPanel onViewDetailedReport={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Close regional summary' }));
    expect(screen.queryByRole('region', { name: 'Regional summary and data note' })).not.toBeInTheDocument();
  });
});
