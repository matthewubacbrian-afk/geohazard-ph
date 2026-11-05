import type { FeatureCollection, MultiPolygon, Polygon, Position } from 'geojson';
import type { HazardEvent } from '../../types/hazard';

export type ActivityRegions = FeatureCollection<Polygon | MultiPolygon>;
export type RegionActivity = { name: string; count: number; sources: Record<string, number>; firstOccurredAt: string | null; lastOccurredAt: string | null };

type BoundedPolygon = { rings: Position[][]; west: number; south: number; east: number; north: number };
const boundaryCache = new WeakMap<ActivityRegions, BoundedPolygon[][]>();

function boundedRegions(boundaries: ActivityRegions): BoundedPolygon[][] {
  const cached = boundaryCache.get(boundaries);
  if (cached) return cached;
  const result = boundaries.features.map(({ geometry }) => {
    const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates;
    return polygons.map((rings) => {
      let west = Infinity, south = Infinity, east = -Infinity, north = -Infinity;
      for (const [x, y] of rings[0] ?? []) {
        west = Math.min(west, x); south = Math.min(south, y);
        east = Math.max(east, x); north = Math.max(north, y);
      }
      return { rings, west, south, east, north };
    });
  });
  boundaryCache.set(boundaries, result);
  return result;
}

// Ray casting with explicit boundary inclusion; holes are excluded.
function inRing(x: number, y: number, ring: Position[]): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [ax, ay] = ring[j];
    const [bx, by] = ring[i];
    const cross = (x - ax) * (by - ay) - (y - ay) * (bx - ax);
    if (Math.abs(cross) < 1e-10 && x >= Math.min(ax, bx) && x <= Math.max(ax, bx)
      && y >= Math.min(ay, by) && y <= Math.max(ay, by)) return true;
    if ((ay > y) !== (by > y) && x < (bx - ax) * (y - ay) / (by - ay) + ax) inside = !inside;
  }
  return inside;
}

function inPolygon(x: number, y: number, rings: Position[][]): boolean {
  return rings.length > 0 && inRing(x, y, rings[0])
    && !rings.slice(1).some((ring) => inRing(x, y, ring));
}

export function buildRegionalActivity(events: HazardEvent[], boundaries: ActivityRegions) {
  const regions: RegionActivity[] = boundaries.features.map((feature) => ({
    name: String(feature.properties?.region_name ?? 'Unnamed region'), count: 0, sources: {}, firstOccurredAt: null, lastOccurredAt: null,
  }));
  const bounded = boundedRegions(boundaries);
  const unique = new Map<string, HazardEvent>();
  for (const event of events) {
    if (event.hazard_type !== 'earthquake') continue;
    const key = event.canonical_id || `${event.source}:${event.external_id || event.id}`;
    if (!unique.has(key) || event.is_primary === true) unique.set(key, event);
  }
  let unassignedCount = 0;
  let invalidCount = 0;
  const times: number[] = [];
  for (const event of unique.values()) {
    const { longitude: x, latitude: y } = event;
    const time = Date.parse(event.occurred_at);
    if (!Number.isFinite(x) || !Number.isFinite(y) || Math.abs(x) > 180
      || Math.abs(y) > 90 || !Number.isFinite(time)) { invalidCount++; continue; }
    times.push(time);
    const index = bounded.findIndex((polygons) => polygons.some((polygon) =>
      x >= polygon.west && x <= polygon.east && y >= polygon.south && y <= polygon.north
      && inPolygon(x, y, polygon.rings),
    ));
    if (index < 0) { unassignedCount++; continue; }
    regions[index].count++;
    const iso = new Date(time).toISOString();
    const region = regions[index];
    if (!region.firstOccurredAt || iso < region.firstOccurredAt) region.firstOccurredAt = iso;
    if (!region.lastOccurredAt || iso > region.lastOccurredAt) region.lastOccurredAt = iso;
    regions[index].sources[event.source] = (regions[index].sources[event.source] ?? 0) + 1;
  }
  const features: ActivityRegions = {
    type: 'FeatureCollection',
    features: boundaries.features.map((feature, index) => ({
      ...feature, properties: { region_name: regions[index].name, event_count: regions[index].count },
    })),
  };
  return {
    regions, features, unassignedCount, invalidCount,
    firstOccurredAt: times.length ? new Date(times.reduce((a, b) => Math.min(a, b))).toISOString() : null,
    lastOccurredAt: times.length ? new Date(times.reduce((a, b) => Math.max(a, b))).toISOString() : null,
  };
}
