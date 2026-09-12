import type { FeatureCollection, MultiPolygon, Polygon } from 'geojson';

import regions from './philippine-regions.json';

export type RegionBoundary = FeatureCollection<Polygon | MultiPolygon>;

export const PHILIPPINE_REGIONS = regions as RegionBoundary;