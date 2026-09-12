import type { Feature, FeatureCollection, MultiPolygon, Polygon } from 'geojson';

import type { RiskProfile } from '../../types/hazard';

type RegionGeometry = Polygon | MultiPolygon;
type RegionFeature = Feature<RegionGeometry>;
type RegionCollection = FeatureCollection<RegionGeometry>;

const REGION_ALIASES: Record<string, string> = {
  armm: 'armm',
  bangsamoro: 'armm',
  car: 'car',
  cordillera: 'car',
  ncr: 'ncr',
  'national capital region': 'ncr',
  palawan: 'mimaropa',
  mimaropa: 'mimaropa',
};

function normalizeRegionName(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  const normalized = value.trim().toLocaleLowerCase();
  return REGION_ALIASES[normalized] ?? normalized;
}

export function riskProfilesToFeatureCollection(
  profiles: RiskProfile[],
  boundaries: RegionCollection,
): RegionCollection {
  const boundaryByName = new Map<string, RegionFeature>();

  for (const boundary of boundaries.features) {
    const name = normalizeRegionName(boundary.properties?.region_name);
    if (name && boundary.geometry) boundaryByName.set(name, boundary);
  }

  const features = profiles.flatMap((profile) => {
    const boundary = boundaryByName.get(normalizeRegionName(profile.region_name) ?? '');
    if (!boundary) return [];

    return [{
      type: 'Feature' as const,
      id: boundary.id,
      geometry: boundary.geometry,
      properties: {
        region_name: profile.region_name,
        label: profile.label,
        confidence: profile.confidence,
        model_version: profile.model_version,
      },
    }];
  });

  return { type: 'FeatureCollection', features };
}