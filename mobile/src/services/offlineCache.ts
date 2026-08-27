const cache = new Map<string, unknown>();

export function saveOfflineValue(key: string, value: unknown) {
  cache.set(key, value);
}

export function readOfflineValue(key: string) {
  return cache.get(key);
}
