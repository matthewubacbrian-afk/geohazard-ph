import { PermissionsAndroid, Platform } from 'react-native';
import { launchCamera } from 'react-native-image-picker';

import type { CapturedSceneImage, SceneAnalysisResult, SceneCandidate, ScenePoint } from '../types/sceneAnalysis';

export const SCENE_ANALYSIS_CAVEAT = 'Visual cues only—not a safety assessment. Verify conditions and follow official emergency guidance.';
export const SCENE_CANDIDATE_HIGHLIGHT = {
  fill: 'rgba(66, 93, 111, 0.24)',
  stroke: '#425d6f',
} as const;
const MAX_IMAGE_BYTES = 4 * 1024 * 1024;
const SURFACE_CLASSES = new Set([
  'floor-other', 'floor-stone', 'floor-tile', 'floor-wood', 'ground-other',
  'road', 'pavement', 'grass', 'gravel',
]);

export class SceneAnalysisError extends Error {
  constructor(message: string, public status: number, public code: string) {
    super(message);
    this.name = 'SceneAnalysisError';
  }
}

export function getRelativeAreaTerm(areaFraction: number, largestAreaFraction: number): number {
  if (!Number.isFinite(areaFraction) || !Number.isFinite(largestAreaFraction) || largestAreaFraction <= 0) {
    return 0;
  }
  return Math.min(Math.max(areaFraction, 0) / largestAreaFraction, 1);
}

export type CaptureOutcome =
  | { status: 'cancelled' }
  | { status: 'captured'; image: CapturedSceneImage }
  | { status: 'error'; message: string };

function decodedBase64Bytes(value: string): number {
  if (!/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value)) return Infinity;
  const padding = value.endsWith('==') ? 2 : value.endsWith('=') ? 1 : 0;
  return value.length * 3 / 4 - padding;
}

export async function captureSceneImage(): Promise<CaptureOutcome> {
  try {
    if (Platform.OS === 'android') {
      const permission = await PermissionsAndroid.request(PermissionsAndroid.PERMISSIONS.CAMERA);
      if (permission !== PermissionsAndroid.RESULTS.GRANTED) {
        return {
          status: 'error',
          message: permission === PermissionsAndroid.RESULTS.NEVER_ASK_AGAIN
            ? 'Camera permission is blocked. Enable camera access in system settings, then try again.'
            : 'Camera permission is needed to capture a scene.',
        };
      }
    }
    const response = await launchCamera({
      mediaType: 'photo',
      includeBase64: true,
      maxWidth: 1600,
      maxHeight: 1600,
      quality: 0.8,
      saveToPhotos: false,
    });
    if (response.didCancel) return { status: 'cancelled' };
    if (response.errorCode) {
      return { status: 'error', message: response.errorCode === 'permission'
        ? 'Camera permission is needed to capture a scene.'
        : 'Could not open the camera. Check camera permission and try again.' };
    }
    const asset = response.assets?.[0];
    if (!asset?.uri || !asset.base64 || asset.type !== 'image/jpeg') {
      return { status: 'error', message: 'The camera did not return a usable JPEG photo. Please try again.' };
    }
    if (decodedBase64Bytes(asset.base64) > MAX_IMAGE_BYTES) {
      return { status: 'error', message: 'This photo is too large to analyze. Capture the scene again.' };
    }
    return {
      status: 'captured',
      image: { uri: asset.uri, imageBase64: asset.base64, width: asset.width ?? 0, height: asset.height ?? 0 },
    };
  } catch {
    return { status: 'error', message: 'Could not open the camera. Check camera permission and try again.' };
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function finiteNumber(value: unknown, min: number, max: number): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max;
}

function mapPoint(value: unknown): ScenePoint {
  if (!isRecord(value) || !finiteNumber(value.x, 0, 1) || !finiteNumber(value.y, 0, 1)) {
    throw new Error('Scene analysis response contains invalid polygon coordinates');
  }
  return { x: value.x, y: value.y };
}

function mapCandidate(value: unknown, index: number): SceneCandidate {
  if (!isRecord(value) || !Number.isInteger(value.rank) || value.rank !== index + 1
    || typeof value.surface_class !== 'string' || !SURFACE_CLASSES.has(value.surface_class)
    || !Array.isArray(value.polygon) || value.polygon.length < 5 || value.polygon.length > 64
    || !finiteNumber(value.area_fraction, 0, 1) || value.area_fraction === 0
    || !finiteNumber(value.compactness, 0, 1) || !finiteNumber(value.model_confidence, 0, 1)
    || !finiteNumber(value.ranking_score, 0, 1)) {
    throw new Error('Scene analysis response contains an invalid candidate');
  }
  const polygon = value.polygon.map(mapPoint);
  const first = polygon[0];
  const last = polygon[polygon.length - 1];
  if (first.x !== last.x || first.y !== last.y
    || new Set(polygon.slice(0, -1).map((point) => `${point.x},${point.y}`)).size < 4) {
    throw new Error('Scene analysis response contains an invalid polygon');
  }
  return {
    rank: value.rank as number,
    surfaceClass: value.surface_class,
    polygon,
    areaFraction: value.area_fraction,
    compactness: value.compactness,
    modelConfidence: value.model_confidence,
    rankingScore: value.ranking_score,
  };
}

export function mapSceneAnalysisResponse(payload: unknown): SceneAnalysisResult {
  if (!isRecord(payload) || typeof payload.model_version !== 'string' || !payload.model_version
    || (payload.result_status !== 'candidates_found' && payload.result_status !== 'no_clear_candidate')
    || !Array.isArray(payload.candidate_regions) || payload.candidate_regions.length > 5
    || !Array.isArray(payload.visual_cues) || !Array.isArray(payload.limitations)
    || payload.limitations.length !== 2 || payload.limitations.some((item) => typeof item !== 'string')) {
    throw new Error('Scene analysis response is invalid');
  }
  const candidateRegions = payload.candidate_regions.map(mapCandidate);
  if ((candidateRegions.length > 0) !== (payload.result_status === 'candidates_found')) {
    throw new Error('Scene analysis response status does not match its candidates');
  }
  const visualCues = payload.visual_cues.map((cue) => {
    if (!isRecord(cue) || typeof cue.class_name !== 'string' || !cue.class_name
      || !finiteNumber(cue.model_confidence, 0, 1)) {
      throw new Error('Scene analysis response contains an invalid visual cue');
    }
    return { className: cue.class_name, modelConfidence: cue.model_confidence };
  });
  return {
    modelVersion: payload.model_version,
    resultStatus: payload.result_status,
    candidateRegions,
    visualCues,
    limitations: payload.limitations as string[],
  };
}

async function readError(response: Response): Promise<SceneAnalysisError> {
  let code = 'request_failed';
  try {
    const body: unknown = await response.json();
    if (isRecord(body) && isRecord(body.error) && typeof body.error.code === 'string') code = body.error.code;
  } catch {
    // Keep response bodies private and surface only a stable generic message.
  }
  const message = code === 'scene_image_too_large'
    ? 'The captured photo is too large. Capture the scene again.'
    : code === 'invalid_scene_image'
      ? 'The captured photo could not be read. Please retake it.'
      : code === 'scene_analysis_unavailable'
        ? 'Scene analysis is temporarily unavailable. Try again later.'
        : 'Could not analyze this scene. Check your connection and try again.';
  return new SceneAnalysisError(message, response.status, code);
}

export async function analyzeScene(baseUrl: string, imageBase64: string, signal?: AbortSignal): Promise<SceneAnalysisResult> {
  if (!baseUrl.trim()) throw new SceneAnalysisError('API URL is not configured', 0, 'not_configured');
  const normalizedBase = baseUrl.replace(/\/+$/, '');
  const endpoint = /\/api\/v1$/i.test(normalizedBase)
    ? `${normalizedBase}/scene-analyses`
    : `${normalizedBase}/api/v1/scene-analyses`;
  let response: Response;
  try {
    response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_base64: imageBase64, mime_type: 'image/jpeg' }),
      signal,
    });
  } catch {
    throw new SceneAnalysisError('Could not connect to scene analysis. Check your connection and try again.', 0, 'network_error');
  }
  if (!response.ok) throw await readError(response);
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new SceneAnalysisError('The scene analysis response could not be read.', response.status, 'invalid_response');
  }
  try {
    return mapSceneAnalysisResponse(payload);
  } catch {
    throw new SceneAnalysisError('The scene analysis response could not be read.', response.status, 'invalid_response');
  }
}
