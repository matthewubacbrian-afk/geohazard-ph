import { ApiError } from '../src/services/api';
import { loadEventFeed } from '../src/services/eventFeed';
import { readOfflineValue, saveOfflineValue } from '../src/services/offlineCache';
import type { HazardEvent } from '../src/types/hazard';

jest.mock('../src/services/api', () => ({
  ...jest.requireActual('../src/services/api'),
  fetchEvents: jest.fn(),
}));

jest.mock('../src/services/offlineCache', () => ({
  readOfflineValue: jest.fn(),
  saveOfflineValue: jest.fn(),
}));

const mockFetchEvents = jest.requireMock('../src/services/api').fetchEvents as jest.Mock;
const mockReadOfflineValue = readOfflineValue as jest.MockedFunction<typeof readOfflineValue>;
const mockSaveOfflineValue = saveOfflineValue as jest.MockedFunction<typeof saveOfflineValue>;

const events = [{
  id: 'event-1',
  hazardType: 'earthquake',
  source: 'usgs',
  externalId: 'event-1',
  magnitude: 4,
  depthKm: 12,
  latitude: 14.6,
  longitude: 121,
  placeName: 'Near Manila',
  occurredAt: '2026-10-09T00:00:00Z',
  alertLevel: null,
  canonicalId: 'event-1',
  isPrimary: true,
  matchConfidence: null,
}] satisfies HazardEvent[];

describe('mobile event feed', () => {
  beforeEach(() => jest.clearAllMocks());

  it('fetches and caches events when the API is available', async () => {
    mockFetchEvents.mockResolvedValue(events);

    await expect(loadEventFeed('https://example.org/api/v1')).resolves.toEqual({
      events,
      isOffline: false,
    });
    expect(mockSaveOfflineValue).toHaveBeenCalledWith('mobile.latestEvents', events);
  });

  it('returns cached events after an API failure', async () => {
    mockFetchEvents.mockRejectedValue(new ApiError('unavailable', 503, 'unavailable'));
    mockReadOfflineValue.mockResolvedValue(events);

    await expect(loadEventFeed('https://example.org/api/v1')).resolves.toEqual({
      events,
      isOffline: true,
    });
  });

  it('rethrows the API failure when no cached event list exists', async () => {
    const error = new ApiError('unavailable', 503, 'unavailable');
    mockFetchEvents.mockRejectedValue(error);
    mockReadOfflineValue.mockResolvedValue(undefined);

    await expect(loadEventFeed('https://example.org/api/v1')).rejects.toBe(error);
  });

  it('ignores cached rows that do not match the mobile event shape', async () => {
    const error = new ApiError('unavailable', 503, 'unavailable');
    mockFetchEvents.mockRejectedValue(error);
    mockReadOfflineValue.mockResolvedValue([{}] as HazardEvent[]);

    await expect(loadEventFeed('https://example.org/api/v1')).rejects.toBe(error);
  });

  it('does not contact the API when its base URL is blank', async () => {
    mockFetchEvents.mockRejectedValue(new ApiError('not configured', 0, 'not_configured'));

    await expect(loadEventFeed('')).rejects.toMatchObject({ code: 'not_configured' });
    expect(mockFetchEvents).not.toHaveBeenCalled();
  });
});
