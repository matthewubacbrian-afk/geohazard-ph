import { ApiError } from '../src/services/api';
import { eventFeedCacheKey, loadCachedEventFeed, loadEventFeed } from '../src/services/eventFeed';
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
    expect(mockSaveOfflineValue).toHaveBeenCalledWith(
      'mobile.latestEvents:https://example.org/api/v1', events,
    );
  });

  it('uses one cache key for equivalent API URL spellings', () => {
    expect(eventFeedCacheKey(' https://example.org/api/v1/ '))
      .toBe(eventFeedCacheKey('https://example.org/api/v1'));
  });

  it('returns cached events after an API failure', async () => {
    mockFetchEvents.mockRejectedValue(new ApiError('unavailable', 503, 'unavailable'));
    mockReadOfflineValue.mockResolvedValue(events);

    await expect(loadEventFeed('https://example.org/api/v1')).resolves.toEqual({
      events,
      isOffline: true,
    });
    expect(mockReadOfflineValue).toHaveBeenCalledWith(
      'mobile.latestEvents:https://example.org/api/v1',
    );
  });

  it('does not reuse server A or legacy events after switching to server B', async () => {
    mockFetchEvents.mockRejectedValue(new ApiError('unavailable', 503, 'unavailable'));
    mockReadOfflineValue.mockImplementation(async (key) => (
      key === 'mobile.latestEvents:https://server-a.example/api/v1' || key === 'mobile.latestEvents'
        ? events : undefined
    ));

    await expect(loadEventFeed('https://server-b.example/api/v1'))
      .rejects.toMatchObject({ code: 'unavailable' });
    expect(mockReadOfflineValue).toHaveBeenCalledTimes(1);
    expect(mockReadOfflineValue).toHaveBeenCalledWith(
      'mobile.latestEvents:https://server-b.example/api/v1',
    );
  });

  it('returns server B cached events when server B is offline', async () => {
    mockFetchEvents.mockRejectedValue(new ApiError('unavailable', 503, 'unavailable'));
    mockReadOfflineValue.mockImplementation(async (key) => (
      key === 'mobile.latestEvents:https://server-b.example/api/v1' ? events : undefined
    ));

    await expect(loadEventFeed(' https://server-b.example/api/v1/ ')).resolves.toEqual({
      events,
      isOffline: true,
    });
  });

  it('treats a cached empty list as a valid offline result', async () => {
    mockFetchEvents.mockRejectedValue(new ApiError('unavailable', 503, 'unavailable'));
    mockReadOfflineValue.mockResolvedValue([]);

    await expect(loadEventFeed('https://example.org/api/v1')).resolves.toEqual({
      events: [],
      isOffline: true,
    });
  });

  it('restores only valid cached rows for the selected server', async () => {
    mockReadOfflineValue.mockImplementation(async (key) => (
      key === 'mobile.latestEvents:https://server-a.example/api/v1'
        ? [events[0], {}] : undefined
    ));

    await expect(loadCachedEventFeed('https://server-a.example/api/v1/'))
      .resolves.toEqual(events);
    await expect(loadCachedEventFeed('https://server-b.example/api/v1'))
      .resolves.toEqual([]);
    await expect(loadCachedEventFeed('')).resolves.toEqual([]);
    expect(mockReadOfflineValue).toHaveBeenCalledTimes(2);
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
