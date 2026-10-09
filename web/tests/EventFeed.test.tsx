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

  it('pins the controlled selection and keeps the rest of the feed visible', () => {
    render(
      <EventFeed
        events={events}
        selectedEvent={events[0]}
        isLoading={false}
        error={null}
        onRetry={() => {}}
        onSelectEvent={() => {}}
        onClearSelection={() => {}}
      />,
    );

    expect(screen.getByRole('button', { name: /Quezon/i })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText('Coordinates')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Batangas/i })).toBeInTheDocument();
    expect(screen.getAllByText('Quezon', { exact: false })).toHaveLength(2);
  });

  it('keeps the selected event pinned when its category filter is disabled', () => {
    render(
      <EventFeed events={events} selectedEvent={events[0]} isLoading={false} error={null}
        onRetry={() => {}} onClearSelection={() => {}} />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Baseline' }));

    expect(screen.getByRole('button', { name: /Quezon/i })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText('Coordinates')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Batangas/i })).not.toBeInTheDocument();
  });

  it('clears controlled selection only through the clear callback', () => {
    const onClearSelection = vi.fn();
    render(<EventFeed events={events} selectedEvent={events[0]} isLoading={false} error={null}
      onRetry={() => {}} onClearSelection={onClearSelection} />);

    fireEvent.click(screen.getByRole('button', { name: 'Close detail' }));

    expect(onClearSelection).toHaveBeenCalledTimes(1);
    expect(screen.getByText('Coordinates')).toBeInTheDocument();
  });

  it('reports another row selection without changing controlled selection until rerender', () => {
    const onSelectEvent = vi.fn();
    const { rerender } = render(<EventFeed events={events} selectedEvent={events[0]} isLoading={false}
      error={null} onRetry={() => {}} onSelectEvent={onSelectEvent} />);

    const eventButton = screen.getByRole('button', { name: /Quezon/i });
    expect(eventButton).toHaveAttribute('aria-pressed', 'true');
    fireEvent.click(screen.getByRole('button', { name: /Batangas/i }));

    expect(eventButton).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: /Batangas/i })).toHaveAttribute('aria-pressed', 'false');
    expect(onSelectEvent).toHaveBeenCalledWith(events[1]);

    rerender(<EventFeed events={events} selectedEvent={events[1]} isLoading={false} error={null}
      onRetry={() => {}} onSelectEvent={onSelectEvent} />);

    expect(screen.getByRole('button', { name: /Quezon/i })).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByRole('button', { name: /Batangas/i })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText('Coordinates')).toBeInTheDocument();
  });

  it('retries a failed event request when activated', () => {
    const onRetry = vi.fn();
    render(<EventFeed events={[]} isLoading={false} error={new Error('offline')} onRetry={onRetry} />);

    fireEvent.click(screen.getByRole('button', { name: /retry/i }));

    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
