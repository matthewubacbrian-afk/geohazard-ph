const mockItems = new Map<string, string>();

jest.mock('@react-native-async-storage/async-storage', () => ({
  __esModule: true,
  default: {
    getItem: jest.fn((key: string) => Promise.resolve(mockItems.get(key) ?? null)),
    setItem: jest.fn((key: string, value: string) => {
      mockItems.set(key, value);
      return Promise.resolve();
    }),
    removeItem: jest.fn((key: string) => {
      mockItems.delete(key);
      return Promise.resolve();
    }),
  },
}), { virtual: true });

import {
  loadSavedLocations,
  saveSavedLocations,
  validateSavedLocation,
} from '../src/services/savedLocations';
import type { SavedLocation } from '../src/types/hazard';

const location: SavedLocation = {
  id: 'location-1',
  name: 'Home',
  latitude: 14.5995,
  longitude: 120.9842,
  radius_km: 25,
};

describe('saved locations', () => {
  beforeEach(() => mockItems.clear());

  it('round-trips saved locations through persistent storage', async () => {
    await saveSavedLocations([location]);

    await expect(loadSavedLocations()).resolves.toEqual([location]);
  });

  it('ignores malformed saved rows without failing the location list', async () => {
    mockItems.set('mobile.savedLocations', JSON.stringify([{
      id: 'broken', name: 7, latitude: 14, longitude: 120, radius_km: 10,
    }]));

    await expect(loadSavedLocations()).resolves.toEqual([]);
  });

  it.each([
    [{ ...location, name: '  ' }, 'name'],
    [{ ...location, latitude: 91 }, 'latitude'],
    [{ ...location, longitude: -181 }, 'longitude'],
    [{ ...location, radius_km: 0 }, 'radius'],
    [{ ...location, radius_km: 501 }, 'radius'],
  ])('rejects invalid %s input', (input, field) => {
    expect(validateSavedLocation(input)).toContain(field);
  });

  it('accepts coordinates at valid geographic and radius limits', () => {
    expect(validateSavedLocation({
      name: 'Dateline', latitude: -90, longitude: 180, radius_km: 500,
    })).toBeNull();
  });
});
