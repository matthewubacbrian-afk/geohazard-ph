import type { HazardEvent, HazardEventWire } from '../types/hazard';

export class ApiError extends Error {
  constructor(message: string, public status: number, public code: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export function mapHazardEvent(row: HazardEventWire): HazardEvent {
  return {
    id: row.id, hazardType: row.hazard_type, source: row.source,
    externalId: row.external_id ?? null, magnitude: row.magnitude, depthKm: row.depth_km,
    latitude: row.latitude, longitude: row.longitude, placeName: row.place_name,
    occurredAt: row.occurred_at, alertLevel: row.alert_level ?? null,
    canonicalId: row.canonical_id ?? null, isPrimary: row.is_primary ?? null,
    matchConfidence: row.match_confidence ?? null,
  };
}

// The application supplies its environment-specific URL at composition time.
export async function fetchEvents(baseUrl: string): Promise<HazardEvent[]> {
  if (!baseUrl) throw new ApiError('API URL is not configured', 0, 'not_configured');
  let response: Response;
  try {
    response = await fetch(`${baseUrl.replace(/\/$/, '')}/events`);
  } catch {
    throw new ApiError('Could not connect to hazard data', 0, 'network_error');
  }
  if (!response.ok) {
    let code = 'request_failed';
    try {
      const body = await response.json();
      if (typeof body?.error?.code === 'string') code = body.error.code;
    } catch {
      // A proxy may return a non-JSON error body.
    }
    throw new ApiError('Could not load hazard data', response.status, code);
  }
  return (await response.json() as HazardEventWire[]).map(mapHazardEvent);
}
