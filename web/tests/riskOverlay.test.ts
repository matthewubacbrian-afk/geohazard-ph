import type { Feature, FeatureCollection, Polygon } from 'geojson';
import { describe, expect, it } from 'vitest';

import type { RiskProfile } from '../src/types/hazard';
import { riskProfilesToFeatureCollection } from '../src/components/map/riskOverlay';

const profiles: RiskProfile[] = [
  {
    region_name: 'Bicol Region',
    cluster: 2,
    label: 'High',
    confidence: 0.82,
    feature_importances: {},
    model_version: 'v1',
    generated_at: '2026-09-12T00:00:00Z',
    dataset_snapshot: 'fixture',
  },
  {
    region_name: 'Eastern Visayas',
    cluster: 1,
    label: 'Moderate',
    confidence: 0.74,
    feature_importances: {},
    model_version: 'v1',
    generated_at: '2026-09-12T00:00:00Z',
    dataset_snapshot: 'fixture',
  },
];

const polygon = (region_name: string, id: string): Feature<Polygon> => ({
  type: 'Feature',
  id,
  properties: { region_name },
  geometry: {
    type: 'Polygon',
    coordinates: [[[120, 10], [121, 10], [121, 11], [120, 10]]],
  },
});

const boundaries: FeatureCollection<Polygon> = {
  type: 'FeatureCollection',
  features: [polygon('bicol region', 'bicol'), polygon('EASTERN VISAYAS', 'ev')],
};

describe('risk overlay conversion', () => {
  it('joins profiles to boundaries case-insensitively and preserves geometry', () => {
    const result = riskProfilesToFeatureCollection(profiles, boundaries);

    expect(result.features).toHaveLength(2);
    expect(result.features[0].geometry).toEqual(boundaries.features[0].geometry);
    expect(result.features[0].properties).toMatchObject({
      region_name: 'Bicol Region',
      label: 'High',
      confidence: 0.82,
      model_version: 'v1',
    });
  });

  it('omits profiles without a matching boundary instead of fabricating geometry', () => {
    const result = riskProfilesToFeatureCollection(
      [{ ...profiles[0], region_name: 'Unknown Region' }],
      boundaries,
    );

    expect(result.features).toHaveLength(0);
  });

  it('maps province-level Palawan profiles to the Mimaropa region boundary', () => {
    const mimaropaBoundary = polygon('Mimaropa', 'mimaropa');
    const result = riskProfilesToFeatureCollection(
      [{ ...profiles[0], region_name: 'Palawan' }],
      { ...boundaries, features: boundaries.features.concat(mimaropaBoundary) },
    );

    expect(result.features).toHaveLength(1);
    expect(result.features[0].properties).toMatchObject({ region_name: 'Palawan' });
    expect(result.features[0].geometry).toEqual(mimaropaBoundary.geometry);
  });
});