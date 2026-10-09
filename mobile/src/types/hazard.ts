export type HazardEventWire = {
  id: string;
  hazard_type: 'earthquake' | 'volcanic' | 'landslide';
  source: string;
  external_id?: string | null;
  magnitude: number | null;
  depth_km: number | null;
  latitude: number;
  longitude: number;
  place_name: string;
  occurred_at: string;
  alert_level?: string | null;
  canonical_id?: string | null;
  is_primary?: boolean | null;
  match_confidence?: number | null;
};

export type HazardEvent = {
  id: string;
  hazardType: HazardEventWire['hazard_type'];
  source: string;
  externalId: string | null;
  magnitude: number | null;
  depthKm: number | null;
  latitude: number;
  longitude: number;
  placeName: string;
  occurredAt: string;
  alertLevel: string | null;
  canonicalId: string | null;
  isPrimary: boolean | null;
  matchConfidence: number | null;
};

export type SavedLocation = {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  radius_km: number;
};

export type NearbyHazard = {
  event: HazardEvent;
  location_id: string;
  distance_km: number;
};
