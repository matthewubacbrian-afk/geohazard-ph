import {
  analyzeScene, captureSceneImage, getRelativeAreaTerm, mapSceneAnalysisResponse,
  SCENE_CANDIDATE_HIGHLIGHT,
} from '../src/services/sceneAnalysis';
import { styles } from '../src/styles';

jest.mock('react-native-image-picker', () => ({ launchCamera: jest.fn() }));
jest.mock('react-native', () => ({
  StyleSheet: { create: (style: object) => style },
  PermissionsAndroid: {
    PERMISSIONS: { CAMERA: 'android.permission.CAMERA' },
    RESULTS: { GRANTED: 'granted', DENIED: 'denied', NEVER_ASK_AGAIN: 'never_ask_again' },
    request: jest.fn(),
  },
  Platform: { OS: 'android' },
}));

import { launchCamera } from 'react-native-image-picker';
import { PermissionsAndroid } from 'react-native';

const validWireResponse = {
  model_version: 'facebook/detr-resnet-50-panoptic@revision',
  result_status: 'candidates_found',
  candidate_regions: [{
    rank: 1,
    surface_class: 'floor-tile',
    polygon: [{ x: 0.1, y: 0.2 }, { x: 0.8, y: 0.2 }, { x: 0.8, y: 0.8 }, { x: 0.1, y: 0.8 }, { x: 0.1, y: 0.2 }],
    area_fraction: 0.42,
    compactness: 0.76,
    model_confidence: 0.91,
    ranking_score: 0.83,
  }],
  visual_cues: [{ class_name: 'chair', model_confidence: 0.88 }],
  limitations: [
    'Visual scene cues only; this result does not determine whether any area is safe.',
    'A single image cannot assess structural stability, hidden or changing hazards, or whether a route is accessible.',
  ],
};

describe('scene analysis mobile service', () => {
  const launch = launchCamera as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
    (PermissionsAndroid.request as jest.Mock).mockResolvedValue(PermissionsAndroid.RESULTS.GRANTED);
  });

  it('normalizes the area ranking term against the largest candidate and handles edge values', () => {
    expect(getRelativeAreaTerm(0.2, 0.5)).toBe(0.4);
    expect(getRelativeAreaTerm(0.8, 0.5)).toBe(1);
    expect(getRelativeAreaTerm(0.5, 0.5)).toBe(1);
    expect(getRelativeAreaTerm(0.2, 0)).toBe(0);
    expect(getRelativeAreaTerm(-0.2, 0.5)).toBe(0);
    expect(getRelativeAreaTerm(Number.POSITIVE_INFINITY, 0.5)).toBe(0);
  });

  it('uses neutral slate candidate highlighting instead of safety-coded green', () => {
    expect(SCENE_CANDIDATE_HIGHLIGHT).toEqual({
      fill: 'rgba(66, 93, 111, 0.24)',
      stroke: '#425d6f',
    });
    expect(styles.candidateButtonSelected).toMatchObject({
      backgroundColor: '#eaf0f3',
      borderColor: '#496273',
    });
  });

  it('returns cancellation without treating it as an error', async () => {
    launch.mockResolvedValue({ didCancel: true });
    await expect(captureSceneImage()).resolves.toEqual({ status: 'cancelled' });
    expect(launch).toHaveBeenCalledWith(expect.objectContaining({
      mediaType: 'photo', includeBase64: true, maxWidth: 1600, maxHeight: 1600,
      quality: 0.8, saveToPhotos: false,
    }));
  });

  it.each([
    ['denied', 'Camera permission is needed'],
    ['never_ask_again', 'Enable camera access in system settings'],
  ])('does not open the camera when Android permission is %s', async (status, message) => {
    (PermissionsAndroid.request as jest.Mock).mockResolvedValue(status);
    await expect(captureSceneImage()).resolves.toMatchObject({ status: 'error', message: expect.stringContaining(message) });
    expect(PermissionsAndroid.request).toHaveBeenCalledWith('android.permission.CAMERA');
    expect(launchCamera).not.toHaveBeenCalled();
  });

  it('returns a bounded JPEG capture and rejects unsupported or oversized assets', async () => {
    launch.mockResolvedValue({ assets: [{ type: 'image/jpeg', base64: 'aGVsbG8=', uri: 'file://private.jpg' }] });
    await expect(captureSceneImage()).resolves.toMatchObject({
      status: 'captured', image: { imageBase64: 'aGVsbG8=', uri: 'file://private.jpg' },
    });
    launch.mockResolvedValue({ assets: [{ type: 'image/png', base64: 'aGVsbG8=', uri: 'file://private.png' }] });
    await expect(captureSceneImage()).resolves.toMatchObject({ status: 'error' });
    launch.mockResolvedValue({ assets: [{ type: 'image/jpeg', base64: 'AAAA'.repeat(1_500_000), uri: 'file://private.jpg' }] });
    await expect(captureSceneImage()).resolves.toMatchObject({ status: 'error' });
    launch.mockResolvedValue({ assets: [] });
    await expect(captureSceneImage()).resolves.toMatchObject({ status: 'error' });
    launch.mockResolvedValue({ errorCode: 'permission' });
    await expect(captureSceneImage()).resolves.toMatchObject({ status: 'error', message: expect.stringContaining('permission') });
    launch.mockRejectedValue(new Error('native detail'));
    await expect(captureSceneImage()).resolves.toMatchObject({ status: 'error' });
  });

  it('posts only the JSON JPEG payload to the shared endpoint and maps every result field', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({ ok: true, json: async () => validWireResponse });
    const log = jest.spyOn(console, 'log').mockImplementation(() => undefined);
    const result = await analyzeScene('https://api.example.test/', 'aGVsbG8=');
    expect(global.fetch).toHaveBeenCalledWith('https://api.example.test/api/v1/scene-analyses', expect.objectContaining({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_base64: 'aGVsbG8=', mime_type: 'image/jpeg' }),
    }));
    expect(result).toEqual({
      modelVersion: validWireResponse.model_version,
      resultStatus: 'candidates_found',
      candidateRegions: [{
        rank: 1, surfaceClass: 'floor-tile', polygon: validWireResponse.candidate_regions[0].polygon,
        areaFraction: 0.42, compactness: 0.76, modelConfidence: 0.91, rankingScore: 0.83,
      }],
      visualCues: [{ className: 'chair', modelConfidence: 0.88 }],
      limitations: validWireResponse.limitations,
    });
    await analyzeScene('https://api.example.test/api/v1/', 'aGVsbG8=');
    expect(global.fetch).toHaveBeenLastCalledWith('https://api.example.test/api/v1/scene-analyses', expect.any(Object));
    expect(log).not.toHaveBeenCalled();
    log.mockRestore();
  });

  it.each([
    [413, 'scene_image_too_large'], [422, 'invalid_scene_image'], [503, 'scene_analysis_unavailable'],
  ])('maps HTTP %i errors without exposing response internals', async (status, code) => {
    (global.fetch as jest.Mock).mockResolvedValue({ ok: false, status, json: async () => ({
      error: { code, message: 'internal path or detail', status },
    }) });
    await expect(analyzeScene('https://api.example.test', 'aGVsbG8=')).rejects.toMatchObject({ code, status });
    await expect(analyzeScene('https://api.example.test', 'aGVsbG8=')).rejects.not.toHaveProperty('message', 'internal path or detail');
    await expect(analyzeScene('', 'aGVsbG8=')).rejects.toMatchObject({ code: 'not_configured' });
    (global.fetch as jest.Mock).mockRejectedValue(new Error('network detail'));
    await expect(analyzeScene('https://api.example.test', 'aGVsbG8=')).rejects.toMatchObject({ code: 'network_error' });
  });

  it('rejects malformed response fields and polygon geometry', () => {
    expect(() => mapSceneAnalysisResponse(validWireResponse)).not.toThrow();
    expect(() => mapSceneAnalysisResponse({ ...validWireResponse, candidate_regions: [{ ...validWireResponse.candidate_regions[0], polygon: [{ x: 2, y: 0 }] }] })).toThrow();
    expect(() => mapSceneAnalysisResponse({ ...validWireResponse, result_status: 'safe' })).toThrow();
  });

  it('maps an empty-candidate response for the explicit no-clear-candidate state', () => {
    const empty = mapSceneAnalysisResponse({ ...validWireResponse, result_status: 'no_clear_candidate', candidate_regions: [] });
    expect(empty.resultStatus).toBe('no_clear_candidate');
    expect(empty.candidateRegions).toEqual([]);
  });
});
