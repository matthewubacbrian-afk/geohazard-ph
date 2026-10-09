const mockItems = new Map<string, string>();

jest.mock('@react-native-async-storage/async-storage', () => ({
  __esModule: true,
  default: {
    getItem: jest.fn((key: string) => Promise.resolve(mockItems.get(key) ?? null)),
    setItem: jest.fn((key: string, value: string) => {
      mockItems.set(key, value);
      return Promise.resolve();
    }),
    removeItem: jest.fn((key: string) => {
      mockItems.delete(key);
      return Promise.resolve();
    }),
  },
}), { virtual: true });

import { readOfflineValue, saveOfflineValue } from '../src/services/offlineCache';

describe('offline cache', () => {
  beforeEach(() => mockItems.clear());

  it('persists a JSON value across independent reads', async () => {
    await saveOfflineValue('latest', [{ id: 'sample' }]);

    await expect(readOfflineValue('latest')).resolves.toEqual([{ id: 'sample' }]);
  });

  it('removes malformed JSON and treats it as a cache miss', async () => {
    mockItems.set('latest', '{');

    await expect(readOfflineValue('latest')).resolves.toBeUndefined();
    expect(mockItems.has('latest')).toBe(false);
  });
});
