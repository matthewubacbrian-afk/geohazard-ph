import { API_BASE_URL } from './client';
import type { EventChange, HazardEvent } from '../types/hazard';

export class RealtimeMessageError extends Error {
  constructor() { super('Invalid realtime event'); this.name = 'RealtimeMessageError'; }
}

export function realtimeUrl(): string {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
  const url = new URL(API_BASE_URL, window.location.origin);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  url.pathname = url.pathname.replace(/\/api\/v1\/?$/, '') + '/ws/events';
  url.search = '';
  url.hash = '';
  return url.toString();
}

export function parseEventChange(data: string): EventChange {
  const value: unknown = JSON.parse(data);
  if (!value || typeof value !== 'object') throw new RealtimeMessageError();
  const row = value as Record<string, unknown>;
  const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  const numberOrNull = (v: unknown) => v === null || (typeof v === 'number' && Number.isFinite(v));
  if (typeof row.id !== 'string' || !uuid.test(row.id) ||
      typeof row.canonical_id !== 'string' || !uuid.test(row.canonical_id) ||
      typeof row.is_primary !== 'boolean' ||
      !['earthquake', 'volcanic', 'landslide'].includes(String(row.hazard_type)) ||
      typeof row.source !== 'string' || typeof row.place_name !== 'string' ||
      !(row.external_id === null || typeof row.external_id === 'string') ||
      !numberOrNull(row.magnitude) || !numberOrNull(row.depth_km) ||
      typeof row.latitude !== 'number' || !Number.isFinite(row.latitude) || Math.abs(row.latitude) > 90 ||
      typeof row.longitude !== 'number' || !Number.isFinite(row.longitude) || Math.abs(row.longitude) > 180 ||
      typeof row.occurred_at !== 'string' || !/(Z|[+-]\d{2}:\d{2})$/.test(row.occurred_at) ||
      !Number.isFinite(Date.parse(row.occurred_at))) throw new RealtimeMessageError();
  return row as EventChange;
}

export function applyEventChange(events: HazardEvent[], change: EventChange): HazardEvent[] {
  const sameRow = (event: HazardEvent) => event.id === change.id ||
    (change.external_id !== null && event.external_id === change.external_id && event.source === change.source);
  const previous = events.find(sameRow);
  const remaining = events.filter((event) =>
    !sameRow(event) &&
    (!change.is_primary || (event.canonical_id ?? event.id) !== change.canonical_id));
  if (change.is_primary) remaining.push({ ...previous, ...change });
  return remaining.sort((a, b) =>
    Date.parse(b.occurred_at) - Date.parse(a.occurred_at) || a.id.localeCompare(b.id));
}
