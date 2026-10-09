import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

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

  it('exposes selected event state accessibly and opens its details', () => {
    const onSelectEvent = vi.fn();
    render(
      <EventFeed events={events} isLoading={false} error={null} onRetry={() => {}}
        onSelectEvent={onSelectEvent} />,
    );

    const eventButton = screen.getByRole('button', { name: /Quezon/i });
    expect(eventButton).toHaveAttribute('aria-pressed', 'false');
    fireEvent.click(eventButton);

    expect(eventButton).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText('Coordinates')).toBeInTheDocument();
    expect(onSelectEvent).toHaveBeenCalledWith(events[0]);
  });

  it('retries a failed event request when activated', () => {
    const onRetry = vi.fn();
    render(<EventFeed events={[]} isLoading={false} error={new Error('offline')} onRetry={onRetry} />);

    fireEvent.click(screen.getByRole('button', { name: /retry/i }));

    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
