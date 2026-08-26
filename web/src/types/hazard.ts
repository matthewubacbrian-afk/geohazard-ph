export type HazardEvent = {
  id: string;
  hazard_type: 'earthquake' | 'volcanic' | 'landslide';
  source: string;
  external_id?: string | null;
  magnitude?: number | null;
  depth_km?: number | null;
  latitude: number;
  longitude: number;
  place_name: string;
  occurred_at: string;
  alert_level?: string | null;
};

export type RiskProfile = {
  region_name: string;
  cluster: number;
  label: string;
  confidence: number;
  feature_importances: Record<string, number>;
  model_version: string;
  generated_at: string;
  dataset_snapshot: string;
};
