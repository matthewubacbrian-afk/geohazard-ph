import { ApiError, fetchEvents, mapHazardEvent } from '../src/services/api';

const wire = {
  id: 'event', hazard_type: 'earthquake' as const, source: 'usgs', external_id: 'source-id',
  magnitude: 0, depth_km: null, latitude: 14, longitude: 121, place_name: 'Test',
  occurred_at: '2026-09-10T00:00:00Z', alert_level: null, canonical_id: 'group',
  is_primary: false, match_confidence: 0,
};

afterEach(() => jest.restoreAllMocks());
describe('hazard API', () => {
  it('maps every wire field and preserves false, zero, and null', () => {
    expect(mapHazardEvent(wire)).toEqual({
      id: 'event', hazardType: 'earthquake', source: 'usgs', externalId: 'source-id',
      magnitude: 0, depthKm: null, latitude: 14, longitude: 121, placeName: 'Test',
      occurredAt: '2026-09-10T00:00:00Z', alertLevel: null, canonicalId: 'group',
      isPrimary: false, matchConfidence: 0,
    });
  });
  it('fetches from the configured URL and maps events', async () => {
    const fetch = jest.spyOn(global, 'fetch').mockResolvedValue({
      ok: true, json: async () => [wire],
    } as Response);
    expect(await fetchEvents('https://example.org/api/v1/')).toEqual([mapHazardEvent(wire)]);
    expect(fetch).toHaveBeenCalledWith('https://example.org/api/v1/events');
  });
  it('reports network and HTTP failures as typed errors', async () => {
    jest.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('offline'));
    await expect(fetchEvents('https://example.org')).rejects.toMatchObject({code: 'network_error'});
    jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: false, status: 503, json: async () => ({error: {code: 'unavailable'}}),
    } as Response);
    await expect(fetchEvents('https://example.org')).rejects.toMatchObject({status: 503, code: 'unavailable'});
    await expect(fetchEvents('')).rejects.toBeInstanceOf(ApiError);
  });
});
