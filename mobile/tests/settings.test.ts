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

import { API_BASE_URL } from '../src/config';
import {
  loadApiBaseUrl,
  saveApiBaseUrl,
  validateApiBaseUrl,
} from '../src/services/settings';

describe('mobile API settings', () => {
  beforeEach(() => mockItems.clear());

  it('uses the configured default when no URL has been saved', async () => {
    await expect(loadApiBaseUrl()).resolves.toBe(API_BASE_URL);
  });

  it('persists a trimmed API base URL without a trailing slash', async () => {
    await saveApiBaseUrl(' https://example.org/api/v1/ ');

    await expect(loadApiBaseUrl()).resolves.toBe('https://example.org/api/v1');
  });

  it.each([
    ['', 'required'],
    ['ftp://example.org/api/v1', 'HTTP or HTTPS'],
    ['https:///api/v1', 'host'],
    ['https://example.org/v2', '/api/v1'],
  ])('rejects %s with a safe setup message', (value, expectedMessage) => {
    expect(validateApiBaseUrl(value)).toContain(expectedMessage);
  });

  it('accepts an HTTP URL with the versioned API path', () => {
    expect(validateApiBaseUrl('http://192.168.1.20:8000/api/v1')).toBeNull();
  });
});
