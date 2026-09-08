import { API_BASE_URL } from './client';
import type { Volcano } from '../types/volcano';

export class VolcanoFeedError extends Error {
  constructor(public status: number) {
    super('Volcano bulletins temporarily unavailable');
    this.name = 'VolcanoFeedError';
  }
}
export async function fetchVolcanoes(signal?: AbortSignal): Promise<Volcano[]> {
  const response = await fetch(`${API_BASE_URL}/volcanoes`, { signal });
  if (!response.ok) throw new VolcanoFeedError(response.status);
  return response.json();
}
