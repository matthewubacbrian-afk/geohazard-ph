import { fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';

vi.mock('../src/hooks/useEvents', () => ({
  useEvents: ({ source }: { source: string }) => {
    const events = [
      {
        id: 'usgs-1',
        hazard_type: 'earthquake',
        source: 'usgs',
        latitude: 12.5,
        longitude: 125.2,
        place_name: 'Eastern Samar',
        occurred_at: '2026-10-14T06:32:00Z',
      },
      {
        id: 'phivolcs-1',
        hazard_type: 'earthquake',
        source: 'phivolcs',
        latitude: 7.1,
        longitude: 126.3,
        place_name: 'Davao Oriental',
        occurred_at: '2026-10-14T04:08:00Z',
      },
      {
        id: 'volcanic-1',
        hazard_type: 'volcanic',
        source: 'phivolcs',
        latitude: 13.2,
        longitude: 123.7,
        place_name: 'Mayon Volcano',
        occurred_at: '2026-10-14T03:00:00Z',
      },
      {
        id: 'landslide-1',
        hazard_type: 'landslide',
        source: 'usgs',
        latitude: 10.2,
        longitude: 125.1,
        place_name: 'Southern Leyte',
        occurred_at: '2026-10-14T01:00:00Z',
      },
    ];

    return {
      data: source ? events.filter((event) => event.source === source) : events,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    };
  },
}));

vi.mock('../src/hooks/useStaticLayers', () => ({
  useStaticLayers: () => ({ data: [], isLoading: false, error: null, refetch: vi.fn() }),
}));

vi.mock('../src/hooks/useRealtimeAlerts', () => ({
  useRealtimeAlerts: () => ({ connected: true, lastUpdated: '2026-10-14T06:30:00Z' }),
}));

vi.mock('../src/components/dashboard/DashboardMapArea', () => ({
  default: ({ events }: { events: unknown[] }) => (
    <div aria-label="Hazard map"><span>{events.length} events in view</span></div>
  ),
}));

vi.mock('../src/components/layout/TopNav', () => ({
  default: ({ status }: { status?: ReactNode }) => <nav aria-label="Main navigation">{status}</nav>,
}));

vi.mock('../src/components/dashboard/DashboardInfoPanel', () => ({
  default: () => <aside aria-label="Regional summary and data note" />,
}));

vi.mock('../src/components/events/EventFeed', () => ({
  default: ({ events }: { events: unknown[] }) => (
    <div data-testid="event-feed">{events.length} events</div>
  ),
}));

vi.mock('../src/components/risk/RiskProfilesPanel', () => ({
  default: () => <div>Risk profile panel</div>,
}));

vi.mock('../src/components/volcanoes/VolcanoPanel', () => ({
  default: () => <div>Volcano panel</div>,
}));

vi.mock('../src/components/map/StaticLayerStatus', () => ({
  default: () => <div>Static layer status</div>,
}));

vi.mock('../src/components/map/VolcanoOverlayStatus', () => ({
  default: () => <div>Volcano overlay status</div>,
}));

import Dashboard from '../src/pages/Dashboard';

function renderDashboard() {
  return render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <Dashboard />
    </MemoryRouter>,
  );
}

describe('Dashboard activity layout', () => {
  it('keeps the event count in view and source filter connected to current query data', () => {
    renderDashboard();

    expect(screen.getByText('4 events in view')).toBeInTheDocument();
    expect(within(screen.getByRole('status')).getByText('LIVE')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'USGS' }));

    expect(screen.getByText('2 events in view')).toBeInTheDocument();
    expect(screen.getByTestId('event-feed')).toHaveTextContent('2 events');
  });

  it('filters all event surfaces by the selected hazard type', () => {
    renderDashboard();

    fireEvent.click(screen.getByLabelText('Earthquake'));

    expect(screen.getByText('2 events in view')).toBeInTheDocument();
    expect(screen.getByTestId('event-feed')).toHaveTextContent('2 events');
  });
});
