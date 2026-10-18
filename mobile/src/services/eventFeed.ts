import { ApiError, fetchEvents } from './api';
import { readOfflineValue, saveOfflineValue } from './offlineCache';
import { normalizeApiBaseUrl } from './settings';
import type { HazardEvent } from '../types/hazard';

const LATEST_EVENTS_KEY_PREFIX = 'mobile.latestEvents:';

export function eventFeedCacheKey(baseUrl: string): string {
  return `${LATEST_EVENTS_KEY_PREFIX}${normalizeApiBaseUrl(baseUrl)}`;
}

async function readCachedEvents(baseUrl: string): Promise<HazardEvent[] | undefined> {
  if (!normalizeApiBaseUrl(baseUrl)) return undefined;
  const cachedEvents = await readOfflineValue<unknown>(eventFeedCacheKey(baseUrl));
  if (!Array.isArray(cachedEvents)) return undefined;
  const validEvents = cachedEvents.filter(isHazardEvent);
  return validEvents.length > 0 || cachedEvents.length === 0 ? validEvents : undefined;
}

export async function loadCachedEventFeed(baseUrl: string): Promise<HazardEvent[]> {
  return await readCachedEvents(baseUrl) ?? [];
}

export type EventFeedResult = {
  events: HazardEvent[];
  isOffline: boolean;
};

export async function loadEventFeed(baseUrl: string): Promise<EventFeedResult> {
  const normalizedUrl = normalizeApiBaseUrl(baseUrl);
  if (!normalizedUrl) {
    throw new ApiError('Enter the API URL to load hazard data', 0, 'not_configured');
  }

  let events: HazardEvent[];
  try {
    events = await fetchEvents(normalizedUrl);
  } catch (error) {
    const cachedEvents = await readCachedEvents(normalizedUrl);
    if (cachedEvents) return { events: cachedEvents, isOffline: true };
    throw error;
  }

  await saveOfflineValue(eventFeedCacheKey(normalizedUrl), events);
  return { events, isOffline: false };
}

export function isHazardEvent(value: unknown): value is HazardEvent {
  if (typeof value !== 'object' || value === null) return false;
  const event = value as Partial<HazardEvent>;
  const hasNullableString = (field: unknown) => field === null || typeof field === 'string';
  const hasNullableNumber = (field: unknown) => field === null
    || (typeof field === 'number' && Number.isFinite(field));

  return typeof event.id === 'string'
    && (event.hazardType === 'earthquake'
      || event.hazardType === 'volcanic'
      || event.hazardType === 'landslide')
    && typeof event.source === 'string'
    && hasNullableString(event.externalId)
    && hasNullableNumber(event.magnitude)
    && hasNullableNumber(event.depthKm)
    && typeof event.latitude === 'number'
    && Number.isFinite(event.latitude)
    && event.latitude >= -90
    && event.latitude <= 90
    && typeof event.longitude === 'number'
    && Number.isFinite(event.longitude)
    && event.longitude >= -180
    && event.longitude <= 180
    && typeof event.placeName === 'string'
    && typeof event.occurredAt === 'string'
    && Number.isFinite(Date.parse(event.occurredAt))
    && hasNullableString(event.alertLevel)
    && hasNullableString(event.canonicalId)
    && (event.isPrimary === null || typeof event.isPrimary === 'boolean')
    && (event.matchConfidence === null
      || (typeof event.matchConfidence === 'number'
        && Number.isFinite(event.matchConfidence)
        && event.matchConfidence >= 0
        && event.matchConfidence <= 1));
}
