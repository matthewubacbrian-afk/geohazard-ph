import { renderToStaticMarkup } from 'react-dom/server';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';

vi.mock('maplibre-gl', () => ({
  default: {
    Map: vi.fn(),
    NavigationControl: vi.fn(),
  },
}));

import DashboardMapArea from '../src/components/dashboard/DashboardMapArea';
import type { EventSummary } from '../src/types/hazard';

function renderCard(summary: EventSummary) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  queryClient.setQueryData(['event-summary'], summary);

  return renderToStaticMarkup(
    <QueryClientProvider client={queryClient}>
      <DashboardMapArea events={[]} />
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
    const html = renderCard(summary);
    expect(html).toContain('4.6');
    expect(html).toContain('7');
  });

  it('shows Not available for classification and dominant fault system', () => {
    const html = renderCard(summary);
    expect(html).toMatch(/Not available/i);
  });
});
