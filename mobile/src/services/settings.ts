import { API_BASE_URL } from '../config';
import { readOfflineValue, saveOfflineValue } from './offlineCache';

const API_BASE_URL_KEY = 'mobile.apiBaseUrl';

export async function loadApiBaseUrl(): Promise<string> {
  const savedUrl = await readOfflineValue<unknown>(API_BASE_URL_KEY);
  if (typeof savedUrl !== 'string' || validateApiBaseUrl(savedUrl) !== null) {
    return API_BASE_URL;
  }
  return normalizeApiBaseUrl(savedUrl);
}

export async function saveApiBaseUrl(value: string): Promise<void> {
  const error = validateApiBaseUrl(value);
  if (error !== null) throw new Error(error);
  await saveOfflineValue(API_BASE_URL_KEY, normalizeApiBaseUrl(value));
}

export function validateApiBaseUrl(value: string): string | null {
  const normalized = normalizeApiBaseUrl(value);
  if (!normalized) return 'API URL is required';
  if (!/^https?:\/\//i.test(normalized)) return 'API URL must use HTTP or HTTPS';

  const match = normalized.match(/^https?:\/\/([^/?#\s]+)(\/[^?#]*)?$/i);
  if (!match) return 'API URL must include a host';
  if ((match[2] ?? '') !== '/api/v1') return 'API URL must end in /api/v1';
  return null;
}

function normalizeApiBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, '');
}
