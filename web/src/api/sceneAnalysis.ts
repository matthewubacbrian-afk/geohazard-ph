import type { SceneAnalysisRequest, SceneAnalysisResponse } from '../types/sceneAnalysis';

export class SceneAnalysisApiError extends Error {
  constructor(message: string, public readonly status: number, public readonly code: string) {
    super(message);
    this.name = 'SceneAnalysisApiError';
  }
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function isSceneResponse(value: unknown): value is SceneAnalysisResponse {
  if (!isObject(value) || typeof value.model_version !== 'string' || !value.model_version ||
      !['candidates_found', 'no_clear_candidate'].includes(String(value.result_status)) ||
      !Array.isArray(value.candidate_regions) || !Array.isArray(value.visual_cues) ||
      !Array.isArray(value.limitations)) return false;
  const candidatesValid = value.candidate_regions.length <= 5 && value.candidate_regions.every((candidate) => {
    if (!isObject(candidate) || typeof candidate.rank !== 'number' || !Number.isInteger(candidate.rank) ||
        candidate.rank < 1 || candidate.rank > 5 ||
        typeof candidate.surface_class !== 'string' ||
        !['floor-other', 'floor-stone', 'floor-tile', 'floor-wood', 'ground-other', 'road', 'pavement', 'grass', 'gravel'].includes(candidate.surface_class) ||
        typeof candidate.area_fraction !== 'number' || candidate.area_fraction <= 0 || candidate.area_fraction > 1 ||
        typeof candidate.compactness !== 'number' || candidate.compactness < 0 || candidate.compactness > 1 ||
        typeof candidate.model_confidence !== 'number' || candidate.model_confidence < 0 || candidate.model_confidence > 1 ||
        typeof candidate.ranking_score !== 'number' || candidate.ranking_score < 0 || candidate.ranking_score > 1 ||
        !Array.isArray(candidate.polygon) || candidate.polygon.length < 5 || candidate.polygon.length > 64) return false;
    const validPoints = candidate.polygon.every((point) => isObject(point) && typeof point.x === 'number' &&
      typeof point.y === 'number' && point.x >= 0 && point.x <= 1 && point.y >= 0 && point.y <= 1);
    if (!validPoints) return false;
    const points = candidate.polygon as { x: number; y: number }[];
    if (points[0].x !== points[points.length - 1].x || points[0].y !== points[points.length - 1].y ||
        new Set(points.slice(0, -1).map((point) => `${point.x},${point.y}`)).size < 4) return false;
    const vertices = points.slice(0, -1);
    const twiceArea = vertices.reduce((sum, point, index) => {
      const next = vertices[(index + 1) % vertices.length];
      return sum + point.x * next.y - next.x * point.y;
    }, 0);
    return twiceArea > 0;
  });
  const cuesValid = value.visual_cues.every((cue) => isObject(cue) &&
    typeof cue.class_name === 'string' && typeof cue.model_confidence === 'number' &&
    cue.model_confidence >= 0 && cue.model_confidence <= 1);
  const limitationsValid = value.limitations.length === 2 &&
    value.limitations[0] === 'Visual scene cues only; this result does not determine whether any area is safe.' &&
    value.limitations[1] === 'A single image cannot assess structural stability, hidden or changing hazards, or whether a route is accessible.';
  return candidatesValid && cuesValid && limitationsValid &&
    (value.candidate_regions.length > 0) === (value.result_status === 'candidates_found');
}

export async function analyzeScene(
  apiBaseUrl: string,
  request: SceneAnalysisRequest,
  signal?: AbortSignal,
): Promise<SceneAnalysisResponse> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl.replace(/\/$/, '')}/scene-analyses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      signal,
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new SceneAnalysisApiError('Could not connect to scene analysis. Check your connection and try again.', 0, 'network_error');
  }
  if (!response.ok) {
    let code = 'scene_analysis_failed';
    try {
      const body: unknown = await response.json();
      if (isObject(body) && isObject(body.error) && typeof body.error.code === 'string') code = body.error.code;
    } catch {
      // Keep the status and safe generic message when a proxy returns a non-JSON response.
    }
    const message = response.status === 413
      ? 'The captured image is too large. Retake it and try again.'
      : response.status === 422
        ? 'The captured image could not be analyzed. Retake it and try again.'
        : response.status === 503
          ? 'Scene analysis is temporarily unavailable. Please try again later.'
          : 'Scene analysis failed. Please try again.';
    throw new SceneAnalysisApiError(message, response.status, code);
  }
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new SceneAnalysisApiError('The scene analysis response was invalid. Please try again.', response.status, 'invalid_response');
  }
  if (!isSceneResponse(payload)) {
    throw new SceneAnalysisApiError('The scene analysis response was invalid. Please try again.', response.status, 'invalid_response');
  }
  return payload;
}
