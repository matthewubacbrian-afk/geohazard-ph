import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../src/components/map/MapView', () => ({
  default: () => <div aria-label="Hazard map" />,
}));

import DashboardMapArea from '../src/components/dashboard/DashboardMapArea';
import type { EventSummary } from '../src/types/hazard';

function renderCard(summary: EventSummary) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  queryClient.setQueryData(['event-summary'], summary);

  return render(
    <QueryClientProvider client={queryClient}>
      <DashboardMapArea
        events={[]}
        isLoading={false}
        error={null}
        onRetry={vi.fn()}
      />
    </QueryClientProvider>,
  );
}

const summary: EventSummary = {
  region_name: 'Test Region',
  event_count: 7,
  avg_magnitude: 4.6,
  max_magnitude: 5.2,
  latest_occurred_at: '2026-08-29T00:00:00Z',
};

describe('Dashboard floating card', () => {
  it('shows the real average magnitude and event frequency from the summary', () => {
    renderCard(summary);
    expect(screen.getAllByText('4.6', { exact: false }).length).toBeGreaterThan(0);
    expect(screen.getAllByText('7', { exact: false }).length).toBeGreaterThan(0);
  });

  it('shows a coming-soon state for classification and dominant fault system', () => {
    renderCard(summary);
    expect(screen.getAllByText(/Coming soon/i).length).toBeGreaterThan(0);
  });
});
