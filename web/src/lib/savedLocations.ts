import type { HazardEvent } from '../types/hazard';

export type LocationPoint = Pick<HazardEvent, 'latitude' | 'longitude'>;
export type SavedLocation = LocationPoint & {
  name: string;
  radius_km: number;
};

export const LOCATION_RADII_KM = [10, 25, 50, 100, 200];
export const DEFAULT_RADIUS_KM = 25;
export const SAVED_LOCATIONS_KEY = 'geohazard.saved-locations.v1';

function isSavedLocation(value: unknown): value is SavedLocation {
  if (!value || typeof value !== 'object') return false;
  const row = value as Partial<SavedLocation>;
  return typeof row.name === 'string' && row.name.trim().length > 0 &&
    typeof row.latitude === 'number' && Math.abs(row.latitude) <= 90 &&
    typeof row.longitude === 'number' && Math.abs(row.longitude) <= 180 &&
    typeof row.radius_km === 'number' && LOCATION_RADII_KM.includes(row.radius_km);
}

export function readSavedLocations(): SavedLocation[] {
  const raw = localStorage.getItem(SAVED_LOCATIONS_KEY);
  if (!raw) return [];
  try {
    const rows: unknown = JSON.parse(raw);
    return Array.isArray(rows) ? rows.filter(isSavedLocation) : [];
  } catch {
    return [];
  }
}

function distanceKm(from: LocationPoint, to: LocationPoint): number {
  const radians = Math.PI / 180;
  const latitudeDelta = (to.latitude - from.latitude) * radians;
  const longitudeDelta = (to.longitude - from.longitude) * radians;
  const haversine = Math.sin(latitudeDelta / 2) ** 2 +
    Math.cos(from.latitude * radians) * Math.cos(to.latitude * radians) *
    Math.sin(longitudeDelta / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(Math.min(1, haversine)));
}

export function findNearbyEarthquakes(events: HazardEvent[], point: LocationPoint, radiusKm: number) {
  return events
    .filter((event) => event.hazard_type === 'earthquake')
    .map((event) => ({ event, distance: distanceKm(point, event) }))
    .filter(({ distance }) => distance <= radiusKm)
    .sort((a, b) => Date.parse(b.event.occurred_at) - Date.parse(a.event.occurred_at));
}
