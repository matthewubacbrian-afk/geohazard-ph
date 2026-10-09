import type { HazardEvent, NearbyHazard, SavedLocation } from '../types/hazard';

const EARTH_RADIUS_KM = 6371;

export function distanceKm(
  latitudeA: number,
  longitudeA: number,
  latitudeB: number,
  longitudeB: number,
): number {
  const latA = toRadians(latitudeA);
  const latB = toRadians(latitudeB);
  const latitudeDelta = latB - latA;
  const longitudeDelta = toRadians(longitudeB - longitudeA);
  const haversine = Math.sin(latitudeDelta / 2) ** 2
    + Math.cos(latA) * Math.cos(latB) * Math.sin(longitudeDelta / 2) ** 2;

  return 2 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(haversine));
}

export function findNearbyHazards(
  events: HazardEvent[],
  locations: SavedLocation[],
): NearbyHazard[] {
  const matches: NearbyHazard[] = [];

  for (const location of locations) {
    for (const event of events) {
      const distance = distanceKm(
        location.latitude,
        location.longitude,
        event.latitude,
        event.longitude,
      );

      if (distance <= location.radius_km + 1e-8) {
        matches.push({ event, location_id: location.id, distance_km: distance });
      }
    }
  }

  return matches.sort((left, right) => left.distance_km - right.distance_km
    || Date.parse(right.event.occurredAt) - Date.parse(left.event.occurredAt));
}

function toRadians(degrees: number): number {
  return (degrees * Math.PI) / 180;
}
