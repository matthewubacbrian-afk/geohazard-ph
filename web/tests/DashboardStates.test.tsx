import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../src/components/map/MapView', () => ({
  default: () => <div aria-label="Hazard map" />,
}));

import DashboardMapArea from '../src/components/dashboard/DashboardMapArea';
import type { HazardEvent } from '../src/types/hazard';

function renderArea({
  events = [],
  isLoading = false,
  error = null,
  onRetry = vi.fn(),
}: {
  events?: HazardEvent[];
  isLoading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <DashboardMapArea
        events={events}
        isLoading={isLoading}
        error={error}
        onRetry={onRetry}
      />
    </QueryClientProvider>,
  );
}

describe('Dashboard map states', () => {
  it('keeps the map visible and shows a loading indicator while events are loading', () => {
    renderArea({ isLoading: true, error: null });
    expect(screen.getByLabelText('Hazard map')).toBeInTheDocument();
    expect(screen.getAllByText(/Loading events/i).length).toBeGreaterThan(0);
  });

  it('keeps the map visible and shows a retry-able error banner when the events request fails', () => {
    renderArea({ isLoading: false, error: new Error('boom') });
    expect(screen.getByLabelText('Hazard map')).toBeInTheDocument();
    expect(screen.getAllByText(/Failed to load events/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Retry/i).length).toBeGreaterThan(0);
  });

  it('renders the map without any status overlay when events load successfully', () => {
    renderArea({ isLoading: false, error: null, events: [] });
    expect(screen.getByLabelText('Hazard map')).toBeInTheDocument();
    expect(screen.queryByText(/Failed to load events/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Loading events/i)).not.toBeInTheDocument();
  });
});
