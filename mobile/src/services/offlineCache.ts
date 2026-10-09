import AsyncStorage from '@react-native-async-storage/async-storage';

export async function saveOfflineValue(key: string, value: unknown): Promise<void> {
  await AsyncStorage.setItem(key, JSON.stringify(value));
}

export async function readOfflineValue<T>(key: string): Promise<T | undefined> {
  const serialized = await AsyncStorage.getItem(key);
  if (serialized === null) return undefined;

  try {
    return JSON.parse(serialized) as T;
  } catch {
    await AsyncStorage.removeItem(key);
    return undefined;
  }
}
