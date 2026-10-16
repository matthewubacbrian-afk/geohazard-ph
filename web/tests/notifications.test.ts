import { afterEach, describe, expect, it } from 'vitest';

import {
  addRealtimeNotification,
  loadNotifications,
  markAllNotificationsRead,
  persistNotifications,
} from '../src/lib/notifications';
import type { EventChange } from '../src/types/hazard';

const change: EventChange = {
  id: '00000000-0000-4000-8000-000000000001',
  canonical_id: '00000000-0000-4000-8000-000000000003',
  is_primary: true,
  hazard_type: 'earthquake',
  source: 'usgs',
  external_id: 'us1',
  magnitude: 4.2,
  depth_km: 12,
  latitude: 12.5,
  longitude: 125.2,
  place_name: 'Eastern Samar',
  occurred_at: '2026-10-14T06:32:00Z',
};

afterEach(() => window.localStorage.clear());

describe('dashboard notification storage', () => {
  it('persists realtime primary events and restores them after reload', () => {
    const first = addRealtimeNotification([], change, '2026-10-14T06:33:00Z');
    persistNotifications(first);

    expect(loadNotifications()).toEqual(first);
  });

  it('deduplicates canonical events and ignores non-primary source rows', () => {
    const first = addRealtimeNotification([], change, '2026-10-14T06:33:00Z');
    const updated = addRealtimeNotification(first, { ...change, magnitude: 4.3 }, '2026-10-14T06:34:00Z');
    const ignored = addRealtimeNotification(updated, { ...change, is_primary: false }, '2026-10-14T06:35:00Z');

    expect(updated).toHaveLength(1);
    expect(updated[0].event.magnitude).toBe(4.3);
    expect(ignored).toEqual(updated);
  });

  it('marks unread notifications read and safely ignores corrupt stored data', () => {
    const items = addRealtimeNotification([], change, '2026-10-14T06:33:00Z');
    const read = markAllNotificationsRead(items, '2026-10-14T06:35:00Z');
    persistNotifications(read);
    expect(loadNotifications()[0].read_at).toBe('2026-10-14T06:35:00Z');

    window.localStorage.setItem('geohazard.notifications.v1', '{bad json');
    expect(loadNotifications()).toEqual([]);
  });
});
