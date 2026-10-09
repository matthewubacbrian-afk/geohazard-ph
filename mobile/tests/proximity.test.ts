import { distanceKm, findNearbyHazards } from '../src/services/proximity';
import type { HazardEvent, SavedLocation } from '../src/types/hazard';

const event = (id: string, latitude: number, longitude: number, occurredAt: string): HazardEvent => ({
  id,
  hazardType: 'earthquake',
  source: 'usgs',
  externalId: id,
  magnitude: 4,
  depthKm: 10,
  latitude,
  longitude,
  placeName: id,
  occurredAt,
  alertLevel: null,
  canonicalId: id,
  isPrimary: true,
  matchConfidence: null,
});

const location: SavedLocation = {
  id: 'home',
  name: 'Home',
  latitude: 0,
  longitude: 0,
  radius_km: 10,
};

describe('proximity matching', () => {
  it('calculates a known one-degree equatorial distance', () => {
    expect(distanceKm(0, 0, 0, 1)).toBeCloseTo(111.195, 2);
  });

  it('includes events on the radius boundary and sorts by distance', () => {
    const boundaryLongitude = location.radius_km / 111.1949266;
    const matches = findNearbyHazards([
      event('boundary', 0, boundaryLongitude, '2026-10-08T00:00:00Z'),
      event('near', 0, 0.01, '2026-10-09T00:00:00Z'),
      event('outside', 0, 0.2, '2026-10-09T00:00:00Z'),
    ], [location]);

    expect(matches.map((match) => match.event.id)).toEqual(['near', 'boundary']);
  });

  it('returns a separate match for each location and uses event time to break distance ties', () => {
    const secondLocation = { ...location, id: 'office', name: 'Office' };
    const matches = findNearbyHazards([
      event('older', 0, 0.01, '2026-10-08T00:00:00Z'),
      event('newer', 0, 0.01, '2026-10-09T00:00:00Z'),
    ], [location, secondLocation]);

    expect(matches.map(({ event: matchedEvent, location_id }) => [matchedEvent.id, location_id]))
      .toEqual([
        ['newer', 'home'], ['newer', 'office'],
        ['older', 'home'], ['older', 'office'],
      ]);
  });
});
