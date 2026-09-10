import { API_BASE_URL } from './client';
import { responseError } from './errors';
import type { StaticLayer, StaticLayerKind } from '../types/staticLayer';

export async function fetchStaticLayers(kind: StaticLayerKind, signal?: AbortSignal): Promise<StaticLayer[]> {
  const response = await fetch(`${API_BASE_URL}/${kind}`, { signal });
  if (!response.ok) throw await responseError(response, 'Failed to load reference layers');
  return response.json();
}
