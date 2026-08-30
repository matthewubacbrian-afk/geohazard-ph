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

  return renderToStaticMarkup(
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
    const html = renderArea({ isLoading: true, error: null });
    expect(html).toContain('aria-label="Hazard map"');
    expect(html).toMatch(/Loading events/i);
  });

  it('keeps the map visible and shows a retry-able error banner when the events request fails', () => {
    const html = renderArea({ isLoading: false, error: new Error('boom') });
    expect(html).toContain('aria-label="Hazard map"');
    expect(html).toMatch(/Failed to load events/i);
    expect(html).toMatch(/Retry/i);
  });

  it('renders the map without any status overlay when events load successfully', () => {
    const html = renderArea({ isLoading: false, error: null, events: [] });
    expect(html).toContain('aria-label="Hazard map"');
    expect(html).not.toMatch(/Failed to load events/i);
    expect(html).not.toMatch(/Loading events/i);
  });
});
