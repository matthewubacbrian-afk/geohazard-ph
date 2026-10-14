import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import NotificationCenter from '../src/components/dashboard/NotificationCenter';
import type { DashboardNotification } from '../src/types/notification';

const notification: DashboardNotification = {
  id: '00000000-0000-4000-8000-000000000003',
  received_at: '2026-10-14T06:33:00Z',
  read_at: null,
  event: {
    id: '00000000-0000-4000-8000-000000000001',
    canonical_id: '00000000-0000-4000-8000-000000000003',
    is_primary: true,
    hazard_type: 'earthquake',
    source: 'phivolcs',
    external_id: 'ph-1',
    magnitude: 4.2,
    depth_km: 12,
    latitude: 12.5,
    longitude: 125.2,
    place_name: 'Eastern Samar',
    occurred_at: '2026-10-14T06:32:00Z',
  },
};

describe('NotificationCenter', () => {
  it('shows persisted notifications, marks a selected item read, and reveals event context', () => {
    const onMarkRead = vi.fn();
    render(
      <NotificationCenter
        notifications={[notification]}
        onMarkRead={onMarkRead}
        onMarkAllRead={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: /Eastern Samar/i }));

    expect(onMarkRead).toHaveBeenCalledWith(notification.id);
    expect(screen.getByText(/M4.2/)).toBeInTheDocument();
    expect(screen.getByText(/12 km/)).toBeInTheDocument();
  });

  it('marks all notifications read and presents a clear empty state', () => {
    const onMarkAllRead = vi.fn();
    const { rerender } = render(
      <NotificationCenter notifications={[notification]} onMarkRead={vi.fn()} onMarkAllRead={onMarkAllRead} />,
    );
    fireEvent.click(screen.getByRole('button', { name: /mark all read/i }));
    expect(onMarkAllRead).toHaveBeenCalledTimes(1);

    rerender(<NotificationCenter notifications={[]} onMarkRead={vi.fn()} onMarkAllRead={onMarkAllRead} />);
    expect(screen.getByText(/No realtime notifications yet/i)).toBeInTheDocument();
  });
});
