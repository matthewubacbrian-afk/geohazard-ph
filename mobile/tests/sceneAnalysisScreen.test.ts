import React from 'react';
import { Image, Pressable, Text } from 'react-native';
import TestRenderer, { act } from 'react-test-renderer';
import type { ReactTestInstance, ReactTestRenderer } from 'react-test-renderer';

import SceneAnalysisScreen from '../src/screens/SceneAnalysisScreen';
import { analyzeScene, captureSceneImage, SceneAnalysisError } from '../src/services/sceneAnalysis';
import type { CaptureOutcome } from '../src/services/sceneAnalysis';
import type { SceneAnalysisResult } from '../src/types/sceneAnalysis';

jest.mock('react-native-image-picker', () => ({ launchCamera: jest.fn() }));
jest.mock('react-native-svg', () => ({ __esModule: true, default: 'Svg', Polygon: 'Polygon' }));
jest.mock('../src/services/sceneAnalysis', () => ({
  ...jest.requireActual('../src/services/sceneAnalysis'),
  captureSceneImage: jest.fn(),
  analyzeScene: jest.fn(),
}));

const capture = jest.mocked(captureSceneImage);
const analyze = jest.mocked(analyzeScene);
const photoA: CaptureOutcome = {
  status: 'captured',
  image: { uri: 'file://scene-a.jpg', imageBase64: 'cGhvdG8tYQ==', width: 800, height: 600 },
};
const photoB: CaptureOutcome = {
  status: 'captured',
  image: { uri: 'file://scene-b.jpg', imageBase64: 'cGhvdG8tYg==', width: 600, height: 800 },
};
const result: SceneAnalysisResult = {
  modelVersion: 'test-model@revision',
  resultStatus: 'candidates_found',
  candidateRegions: [{
    rank: 1, surfaceClass: 'floor-tile', areaFraction: 0.4, compactness: 0.7,
    modelConfidence: 0.8, rankingScore: 0.6,
    polygon: [{ x: 0, y: 0 }, { x: 1, y: 0 }, { x: 1, y: 1 }, { x: 0, y: 0 }],
  }],
  visualCues: [{ className: 'chair', modelConfidence: 0.8 }],
  limitations: ['Visual cues do not determine safety.'],
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((complete) => { resolve = complete; });
  return { promise, resolve };
}

describe('SceneAnalysisScreen replacement controls', () => {
  let screen: ReactTestRenderer;

  function texts() {
    return screen.root.findAllByType(Text).map((node) => node.props.children);
  }

  function buttons(label: string) {
    return screen.root.findAllByType(Pressable).filter((node) =>
      node.findAllByType(Text).some((text) => text.props.children === label));
  }

  function button(label: string): ReactTestInstance {
    const matches = buttons(label);
    expect(matches).toHaveLength(1);
    return matches[0];
  }

  async function press(label: string) {
    const control = button(label);
    expect(control.props.disabled).not.toBe(true);
    await act(async () => { control.props.onPress(); });
  }

  async function showPreview() {
    await press('Open camera');
    expect(screen.root.findAllByType(Image).map((node) => node.props.source.uri))
      .toEqual(['file://scene-a.jpg']);
  }

  beforeEach(() => {
    jest.resetAllMocks();
    capture.mockResolvedValue(photoA);
    analyze.mockResolvedValue(result);
    act(() => {
      screen = TestRenderer.create(React.createElement(SceneAnalysisScreen, {
        apiBaseUrl: 'https://api.example.test', isActive: true,
      }));
    });
  });

  afterEach(() => { act(() => { screen.unmount(); }); });

  it('offers one enabled Retake immediately after capture, before analysis', async () => {
    await showPreview();
    expect(button('Retake photo').props.disabled).toBe(false);
    expect(buttons('Retake blurry photo')).toHaveLength(0);
    expect(analyze).not.toHaveBeenCalled();
  });

  it('clears the old preview while replacement capture is still pending', async () => {
    await showPreview();
    const pending = deferred<CaptureOutcome>();
    capture.mockReturnValueOnce(pending.promise);
    await press('Retake photo');
    expect(screen.root.findAllByType(Image)).toHaveLength(0);
    expect(button('Opening camera…').props.disabled).toBe(true);
    expect(buttons('Analyze captured scene')).toHaveLength(0);
    await act(async () => { pending.resolve(photoB); });
    expect(screen.root.findAllByType(Image).map((node) => node.props.source.uri))
      .toEqual(['file://scene-b.jpg']);
    await press('Analyze captured scene');
    expect(analyze).toHaveBeenLastCalledWith(
      'https://api.example.test', 'cGhvdG8tYg==', expect.any(AbortSignal), false,
    );
  });

  it('returns to the empty Open camera state when retake is cancelled', async () => {
    await showPreview();
    capture.mockResolvedValueOnce({ status: 'cancelled' });
    await press('Retake photo');
    expect(screen.root.findAllByType(Image)).toHaveLength(0);
    expect(button('Open camera').props.disabled).toBe(false);
    expect(buttons('Retake photo')).toHaveLength(0);
    expect(buttons('Analyze captured scene')).toHaveLength(0);
  });

  it.each([
    new SceneAnalysisError('Scene analysis is temporarily unavailable.', 503, 'scene_analysis_unavailable'),
    new SceneAnalysisError('Check your connection and try again.', 0, 'network_error'),
    new SceneAnalysisError('API URL is not configured', 0, 'not_configured'),
  ])('keeps Retake after $code and clears the error before replacement resolves', async (error) => {
    await showPreview();
    analyze.mockRejectedValueOnce(error);
    await press('Analyze captured scene');
    expect(texts()).toContain(error.message);
    expect(button('Retake photo').props.disabled).toBe(false);
    const pending = deferred<CaptureOutcome>();
    capture.mockReturnValueOnce(pending.promise);
    await press('Retake photo');
    expect(texts()).not.toContain(error.message);
    expect(screen.root.findAllByType(Image)).toHaveLength(0);
    await act(async () => { pending.resolve({ status: 'cancelled' }); });
    expect(button('Open camera').props.disabled).toBe(false);
  });

  it('disables Retake until a pending analysis completes', async () => {
    await showPreview();
    const pending = deferred<SceneAnalysisResult>();
    analyze.mockReturnValueOnce(pending.promise);
    await press('Analyze captured scene');
    expect(button('Retake photo').props.disabled).toBe(true);
    expect(capture).toHaveBeenCalledTimes(1);
    await act(async () => { pending.resolve(result); });
    expect(button('Retake photo').props.disabled).toBe(false);
    expect(texts()).toContain('Evidence checklist');
  });

  it('preserves warning continuation and uses one guarded warning Retake', async () => {
    await showPreview();
    analyze.mockRejectedValueOnce(new SceneAnalysisError('Blurry photo', 422, 'scene_image_quality_warning'));
    await press('Analyze captured scene');
    expect(button('Retake blurry photo').props.disabled).toBe(false);
    expect(buttons('Retake photo')).toHaveLength(0);
    const pending = deferred<SceneAnalysisResult>();
    analyze.mockReturnValueOnce(pending.promise);
    await press('Continue anyway');
    expect(analyze).toHaveBeenLastCalledWith(
      'https://api.example.test', 'cGhvdG8tYQ==', expect.any(AbortSignal), true,
    );
    expect(button('Retake photo').props.disabled).toBe(true);
    await act(async () => { pending.resolve(result); });
    expect(texts()).toContain('Evidence checklist');
  });

  it('clears the warning when retaking instead of continuing', async () => {
    await showPreview();
    analyze.mockRejectedValueOnce(new SceneAnalysisError('Blurry photo', 422, 'scene_image_quality_warning'));
    await press('Analyze captured scene');
    const pending = deferred<CaptureOutcome>();
    capture.mockReturnValueOnce(pending.promise);
    await press('Retake blurry photo');
    expect(buttons('Continue anyway')).toHaveLength(0);
    expect(buttons('Retake blurry photo')).toHaveLength(0);
    await act(async () => { pending.resolve(photoB); });
    expect(button('Retake photo').props.disabled).toBe(false);
  });

  it('clears the result and overlay immediately when retaking a reviewed photo', async () => {
    await showPreview();
    await press('Analyze captured scene');
    expect(texts()).toContain('Evidence checklist');
    expect(screen.root.findAllByType('Svg')).toHaveLength(1);
    const pending = deferred<CaptureOutcome>();
    capture.mockReturnValueOnce(pending.promise);
    await press('Retake photo');
    expect(texts()).not.toContain('Evidence checklist');
    expect(screen.root.findAllByType(Image)).toHaveLength(0);
    expect(screen.root.findAllByType('Svg')).toHaveLength(0);
    await act(async () => { pending.resolve(photoB); });
    expect(button('Analyze captured scene').props.disabled).toBe(false);
  });
});
