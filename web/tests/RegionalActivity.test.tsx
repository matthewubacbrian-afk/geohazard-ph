import { describe, expect, it } from 'vitest';
import type { FeatureCollection, Polygon, MultiPolygon } from 'geojson';
import type { HazardEvent } from '../src/types/hazard';
import { buildRegionalActivity } from '../src/components/map/regionalActivity';

const boundaries: FeatureCollection<Polygon | MultiPolygon> = {
  type: 'FeatureCollection', features: [
    { type: 'Feature', properties: { region_name: 'First' }, geometry: {
      type: 'Polygon', coordinates: [
        [[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]],
        [[1, 1], [2, 1], [2, 2], [1, 2], [1, 1]],
      ],
    } },
    { type: 'Feature', properties: { region_name: 'Second' }, geometry: {
      type: 'MultiPolygon', coordinates: [[[[6, 0], [8, 0], [8, 2], [6, 2], [6, 0]]]],
    } },
  ],
};
const event = (id: string, longitude: number, latitude: number, extra = {}): HazardEvent => ({
  id, longitude, latitude, hazard_type: 'earthquake', source: 'phivolcs',
  occurred_at: '2026-11-01T00:00:00Z', place_name: 'Example', ...extra,
});

describe('recorded regional activity', () => {
  it('counts valid earthquakes inside polygons, including separate islands, without inventing offshore assignments', () => {
    const result = buildRegionalActivity([
      event('inside', 3, 3), event('edge', 0, 2), event('hole', 1.5, 1.5),
      event('island', 7, 1), event('offshore', 5, 5),
      event('volcano', 3, 3, { hazard_type: 'volcanic' }),
      event('invalid', NaN, 3), event('bad-date', 3, 3, { occurred_at: 'invalid' }),
    ], boundaries);
    expect(result.regions.map((region) => region.count)).toEqual([2, 1]);
    expect(result.unassignedCount).toBe(2);
    expect(result.invalidCount).toBe(2);
    expect(result.regions[0].sources).toEqual({ phivolcs: 2 });
  });

  it('counts a canonical earthquake once and records the observed dates', () => {
    const result = buildRegionalActivity([
      event('a', 3, 3, { canonical_id: 'same', source: 'usgs', is_primary: false }),
      event('b', 3, 3, { canonical_id: 'same', is_primary: true }),
      event('c', 3, 3, { occurred_at: '2026-11-03T00:00:00Z' }),
    ], boundaries);
    expect(result.regions[0].count).toBe(2);
    expect(result.regions[0].sources).toEqual({ phivolcs: 2 });
    expect(result.firstOccurredAt).toBe('2026-11-01T00:00:00.000Z');
    expect(result.lastOccurredAt).toBe('2026-11-03T00:00:00.000Z');
  });

  it('retains all empty regions without a low-risk label or classifier confidence', () => {
    const result = buildRegionalActivity([], boundaries);
    expect(result.regions.map((region) => region.count)).toEqual([0, 0]);
    expect(result.firstOccurredAt).toBeNull();
    expect(result.features.features[0].properties).toEqual({ region_name: 'First', event_count: 0 });
  });
});

