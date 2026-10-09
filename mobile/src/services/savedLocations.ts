import { readOfflineValue, saveOfflineValue } from './offlineCache';
import type { SavedLocation } from '../types/hazard';

const SAVED_LOCATIONS_KEY = 'mobile.savedLocations';

export async function loadSavedLocations(): Promise<SavedLocation[]> {
  const saved = await readOfflineValue<unknown>(SAVED_LOCATIONS_KEY);
  if (!Array.isArray(saved)) return [];

  return saved.filter(isSavedLocation);
}

export async function saveSavedLocations(locations: SavedLocation[]): Promise<void> {
  await saveOfflineValue(SAVED_LOCATIONS_KEY, locations);
}

export function validateSavedLocation(input: Omit<SavedLocation, 'id'>): string | null {
  if (!input.name.trim()) return 'name is required';
  if (!Number.isFinite(input.latitude) || input.latitude < -90 || input.latitude > 90) {
    return 'latitude must be between -90 and 90';
  }
  if (!Number.isFinite(input.longitude) || input.longitude < -180 || input.longitude > 180) {
    return 'longitude must be between -180 and 180';
  }
  if (!Number.isFinite(input.radius_km) || input.radius_km < 1 || input.radius_km > 500) {
    return 'radius must be between 1 and 500 km';
  }
  return null;
}

function isSavedLocation(value: unknown): value is SavedLocation {
  if (typeof value !== 'object' || value === null) return false;
  const location = value as Partial<SavedLocation>;
  if (typeof location.id !== 'string'
      || typeof location.name !== 'string'
      || typeof location.latitude !== 'number'
      || typeof location.longitude !== 'number'
      || typeof location.radius_km !== 'number') {
    return false;
  }

  return validateSavedLocation({
    name: location.name,
    latitude: location.latitude,
    longitude: location.longitude,
    radius_km: location.radius_km,
  }) === null;
}
