import { ApiError, fetchEvents } from './api';
import { readOfflineValue, saveOfflineValue } from './offlineCache';
import type { HazardEvent } from '../types/hazard';

const LATEST_EVENTS_KEY = 'mobile.latestEvents';

export type EventFeedResult = {
  events: HazardEvent[];
  isOffline: boolean;
};

export async function loadEventFeed(baseUrl: string): Promise<EventFeedResult> {
  const normalizedUrl = baseUrl.trim();
  if (!normalizedUrl) {
    throw new ApiError('Enter the API URL to load hazard data', 0, 'not_configured');
  }

  let events: HazardEvent[];
  try {
    events = await fetchEvents(normalizedUrl);
  } catch (error) {
    const cachedEvents = await readOfflineValue<unknown>(LATEST_EVENTS_KEY);
    if (Array.isArray(cachedEvents)) {
      const validEvents = cachedEvents.filter(isHazardEvent);
      if (validEvents.length === cachedEvents.length || validEvents.length > 0) {
        return { events: validEvents, isOffline: true };
      }
    }
    throw error;
  }

  await saveOfflineValue(LATEST_EVENTS_KEY, events);
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
