import type { LineString, MultiLineString, Polygon, MultiPolygon } from 'geojson';

export type StaticLayer = {
  id: string;
  external_id: string;
  name: string;
  source: 'gem' | 'phivolcs';
  source_url: string;
  license_name: string;
  dataset_version: string;
  imported_at: string;
  source_properties: Record<string, unknown>;
  geometry: LineString | MultiLineString | Polygon | MultiPolygon;
};
export type StaticLayerKind = 'faults' | 'volcano-zones';
