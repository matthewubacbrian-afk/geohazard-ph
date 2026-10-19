import { ApiError, fetchEvents } from './api';
import { readOfflineValue, saveOfflineValue } from './offlineCache';
import { normalizeApiBaseUrl } from './settings';
import type { HazardEvent } from '../types/hazard';

const LATEST_EVENTS_KEY_PREFIX = 'mobile.latestEvents:';
const latestRequestByUrl = new Map<string, symbol>();
const pendingWriteByKey = new Map<string, Promise<void>>();

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

async function saveCurrentEvents(
  baseUrl: string,
  requestToken: symbol,
  events: HazardEvent[],
): Promise<void> {
  if (latestRequestByUrl.get(baseUrl) !== requestToken) return;

  const key = eventFeedCacheKey(baseUrl);
  const previousWrite = pendingWriteByKey.get(key) ?? Promise.resolve();
  const nextWrite = previousWrite.catch(() => undefined).then(async () => {
    if (latestRequestByUrl.get(baseUrl) === requestToken) {
      await saveOfflineValue(key, events);
    }
  });
  pendingWriteByKey.set(key, nextWrite);
  try {
    await nextWrite;
  } finally {
    if (pendingWriteByKey.get(key) === nextWrite) pendingWriteByKey.delete(key);
  }
}

export async function loadEventFeed(baseUrl: string): Promise<EventFeedResult> {
  const normalizedUrl = normalizeApiBaseUrl(baseUrl);
  if (!normalizedUrl) {
    throw new ApiError('Enter the API URL to load hazard data', 0, 'not_configured');
  }

  const requestToken = Symbol('event-feed-request');
  latestRequestByUrl.set(normalizedUrl, requestToken);
  try {
    let events: HazardEvent[];
    try {
      events = await fetchEvents(normalizedUrl);
    } catch (error) {
      const cachedEvents = await readCachedEvents(normalizedUrl);
      if (cachedEvents) return { events: cachedEvents, isOffline: true };
      throw error;
    }

    await saveCurrentEvents(normalizedUrl, requestToken, events);
    return { events, isOffline: false };
  } finally {
    if (latestRequestByUrl.get(normalizedUrl) === requestToken) {
      latestRequestByUrl.delete(normalizedUrl);
    }
  }
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
