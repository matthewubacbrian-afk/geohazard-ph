export type Volcano = {
  id: string;
  name: string;
  latitude: number | null;
  longitude: number | null;
  current_alert_level: number | null;
  source: 'phivolcs';
  source_url: string | null;
  bulletin_url: string | null;
  bulletin_at: string | null;
  retrieved_at: string | null;
  stale: boolean;
};
