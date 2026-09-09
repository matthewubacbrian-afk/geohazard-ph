import { afterEach, describe, expect, it, vi } from 'vitest';

import { fetchEvents } from '../src/api/client';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('fetchEvents', () => {
  it('encodes supported event filters in the backend request', async () => {
    const response = {
      ok: true,
      json: vi.fn().mockResolvedValue([]),
    } as unknown as Response;
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response);

    await fetchEvents({ source: 'phivolcs', since: '2026-09-01T00:00:00Z' });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/events?'),
      expect.objectContaining({ signal: undefined }),
    );
    const requestUrl = new URL(String(fetchMock.mock.calls[0][0]));
    expect(Object.fromEntries(requestUrl.searchParams)).toEqual({
      source: 'phivolcs',
      since: '2026-09-01T00:00:00Z',
    });
  });
});
