import { renderToStaticMarkup } from 'react-dom/server';
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
    const html = renderToStaticMarkup(
      <EventFeed events={events} isLoading={false} error={null} onRetry={() => {}} />,
    );

    expect(html).toMatch(/Regional activity/i);
    expect(html).toMatch(/2 events/i);
  });

  it('renders each event with its place name', () => {
    const html = renderToStaticMarkup(
      <EventFeed events={events} isLoading={false} error={null} onRetry={() => {}} />,
    );

    expect(html).toContain('Quezon');
    expect(html).toContain('Batangas');
  });

  it('shows skeletons instead of events while loading', () => {
    const html = renderToStaticMarkup(
      <EventFeed events={events} isLoading error={null} onRetry={() => {}} />,
    );

    expect(html).toMatch(/aria-hidden="true"/);
    expect(html).not.toContain('Quezon');
  });

  it('shows an empty state when no events match', () => {
    const html = renderToStaticMarkup(
      <EventFeed events={[]} isLoading={false} error={null} onRetry={() => {}} />,
    );

    expect(html).toMatch(/No events match the current filters/i);
  });
});
