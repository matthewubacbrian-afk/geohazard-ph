import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import EventFeed from '../src/components/events/EventFeed';
import type { HazardEvent } from '../src/types/hazard';

const events: HazardEvent[] = [
  {
    id: 'e1',
    hazard_type: 'earthquake',
    source: 'USGS',
    magnitude: 5.2,
    depth_km: 20,
    latitude: 13.5,
    longitude: 121.5,
    place_name: 'Quezon',
    occurred_at: '2026-08-29T00:00:00Z',
    alert_level: 'critical',
  },
  {
    id: 'e2',
    hazard_type: 'earthquake',
    source: 'PHIVOLCS',
    magnitude: 3.4,
    depth_km: 10,
    latitude: 14,
    longitude: 122,
    place_name: 'Batangas',
    occurred_at: '2026-08-28T00:00:00Z',
    alert_level: 'baseline',
  },
];

describe('EventFeed', () => {
  it('shows the activity header and event count', () => {
    render(
      <EventFeed events={events} isLoading={false} error={null} onRetry={() => {}} />,
    );

    expect(screen.getAllByText(/Regional activity/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/2 events/i).length).toBeGreaterThan(0);
  });

  it('renders each event with its place name', () => {
    render(
      <EventFeed events={events} isLoading={false} error={null} onRetry={() => {}} />,
    );

    expect(screen.getAllByText('Quezon', { exact: false }).length).toBeGreaterThan(0);
    expect(screen.getAllByText('Batangas', { exact: false }).length).toBeGreaterThan(0);
  });

  it('shows skeletons instead of events while loading', () => {
    render(
      <EventFeed events={events} isLoading error={null} onRetry={() => {}} />,
    );

    expect(screen.queryByText('Quezon')).not.toBeInTheDocument();
    expect(screen.queryByText('Quezon', { exact: false })).not.toBeInTheDocument();
  });

  it('shows an empty state when no events match', () => {
    render(
      <EventFeed events={[]} isLoading={false} error={null} onRetry={() => {}} />,
    );

    expect(screen.getAllByText(/No events match the current filters/i).length).toBeGreaterThan(0);
  });
});
