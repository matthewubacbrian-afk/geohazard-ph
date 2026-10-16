import type { DashboardNotification } from '../types/notification';
import type { EventChange } from '../types/hazard';

export const NOTIFICATION_STORAGE_KEY = 'geohazard.notifications.v1';
export const MAX_STORED_NOTIFICATIONS = 50;

function isEventChange(value: unknown): value is EventChange {
  if (!value || typeof value !== 'object') return false;
  const event = value as Record<string, unknown>;
  return typeof event.id === 'string' && typeof event.canonical_id === 'string' &&
    event.is_primary === true &&
    ['earthquake', 'volcanic', 'landslide'].includes(String(event.hazard_type)) &&
    typeof event.source === 'string' && typeof event.place_name === 'string' &&
    typeof event.latitude === 'number' && Number.isFinite(event.latitude) &&
    typeof event.longitude === 'number' && Number.isFinite(event.longitude) &&
    typeof event.occurred_at === 'string' && Number.isFinite(Date.parse(event.occurred_at)) &&
    (event.magnitude === null || typeof event.magnitude === 'number') &&
    (event.depth_km === null || typeof event.depth_km === 'number') &&
    (event.external_id === null || typeof event.external_id === 'string');
}

function isDashboardNotification(value: unknown): value is DashboardNotification {
  if (!value || typeof value !== 'object') return false;
  const notification = value as Record<string, unknown>;
  return typeof notification.id === 'string' && isEventChange(notification.event) &&
    typeof notification.received_at === 'string' && Number.isFinite(Date.parse(notification.received_at)) &&
    (notification.read_at === null || (typeof notification.read_at === 'string' &&
      Number.isFinite(Date.parse(notification.read_at))));
}

export function loadNotifications(storage?: Storage): DashboardNotification[] {
  try {
    const currentStorage = storage ?? window.localStorage;
    const raw = currentStorage.getItem(NOTIFICATION_STORAGE_KEY);
    if (!raw) return [];
    const value: unknown = JSON.parse(raw);
    if (!Array.isArray(value)) return [];
    return value.filter(isDashboardNotification)
      .sort((a, b) => Date.parse(b.received_at) - Date.parse(a.received_at))
      .slice(0, MAX_STORED_NOTIFICATIONS);
  } catch {
    return [];
  }
}

export function persistNotifications(
  notifications: DashboardNotification[],
  storage?: Storage,
): void {
  try {
    (storage ?? window.localStorage).setItem(
      NOTIFICATION_STORAGE_KEY,
      JSON.stringify(notifications.slice(0, MAX_STORED_NOTIFICATIONS)),
    );
  } catch {
    // Storage may be disabled or full; realtime event delivery must continue to work.
  }
}

export function addRealtimeNotification(
  notifications: DashboardNotification[],
  event: EventChange,
  receivedAt: string,
): DashboardNotification[] {
  if (!event.is_primary) return notifications;
  const existing = notifications.find((item) => item.id === event.canonical_id);
  const next: DashboardNotification = {
    id: event.canonical_id,
    event,
    received_at: receivedAt,
    read_at: existing?.read_at ?? null,
  };
  return [next, ...notifications.filter((item) => item.id !== event.canonical_id)]
    .sort((a, b) => Date.parse(b.received_at) - Date.parse(a.received_at))
    .slice(0, MAX_STORED_NOTIFICATIONS);
}

export function markNotificationRead(
  notifications: DashboardNotification[],
  id: string,
  readAt = new Date().toISOString(),
): DashboardNotification[] {
  return notifications.map((item) => item.id === id && item.read_at === null
    ? { ...item, read_at: readAt }
    : item);
}

export function markAllNotificationsRead(
  notifications: DashboardNotification[],
  readAt = new Date().toISOString(),
): DashboardNotification[] {
  return notifications.map((item) => item.read_at === null ? { ...item, read_at: readAt } : item);
}
