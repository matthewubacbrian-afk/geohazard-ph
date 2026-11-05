import type { SceneAnalysisRequest, SceneAnalysisResponse } from '../types/sceneAnalysis';

type Progress = (message: string) => void;
const MESSAGES: Record<string, string> = {
  decoding: 'Preparing the photo on your device…',
  loading: 'Loading the model on your device. First use downloads about 44 MB plus the runtime…',
  analyzing: 'Analyzing on your device. This can take a minute on slower devices…',
};

export function createBrowserSceneAnalyzer(makeWorker = () => new Worker(
  new URL('./sceneAnalysis.worker.ts', import.meta.url), { type: 'module' },
)) {
  let worker: Worker | null = null;
  let sequence = 0;
  let cancelActive: (() => void) | null = null;
  function dispose() {
    cancelActive?.();
    worker?.terminate(); worker = null;
  }
  function analyze(request: SceneAnalysisRequest, signal: AbortSignal, progress?: Progress): Promise<SceneAnalysisResponse> {
    if (signal.aborted) return Promise.reject(new DOMException('Analysis cancelled', 'AbortError'));
    if (cancelActive) return Promise.reject(new Error('An image is already being analyzed.'));
    try { worker ??= makeWorker(); } catch {
      return Promise.reject(new Error('On-device analysis is not supported in this browser. Try a recent Chrome, Edge, or Firefox browser.'));
    }
    const current = worker, id = ++sequence;
    return new Promise((resolve, reject) => {
      const cleanup = () => {
        clearTimeout(timeout); signal.removeEventListener('abort', abort);
        current.onmessage = null; current.onerror = null; cancelActive = null;
      };
      const fail = (error: Error) => {
        cleanup(); current.terminate(); if (worker === current) worker = null; reject(error);
      };
      const abort = () => fail(new DOMException('Analysis cancelled', 'AbortError'));
      const timeout = setTimeout(() => fail(new Error('On-device analysis took too long. Try a smaller scene or a faster device.')), 180_000);
      cancelActive = abort;
      signal.addEventListener('abort', abort, { once: true });
      current.onerror = (event) => {
        event.preventDefault();
        fail(new Error('On-device analysis could not start. Check your connection for the initial model download, or try another browser.'));
      };
      current.onmessage = ({ data }) => {
        if (data.id !== id) return;
        if (data.type === 'progress') { progress?.(MESSAGES[data.phase] ?? MESSAGES.analyzing); return; }
        if (data.type === 'result') { cleanup(); resolve(data.result as SceneAnalysisResponse); return; }
        if (data.type === 'error') {
          const error = new Error(data.code === 'scene_image_quality_warning'
            ? 'This photo may be blurry. Retake it or continue with reduced reliability.'
            : data.code === 'invalid_scene_image' ? 'The captured JPEG could not be read. Retake the photo.'
            : 'On-device analysis is unavailable. Check the initial download connection, or try a faster device or another browser.');
          Object.assign(error, { code: data.code }); fail(error);
        }
      };
      try { current.postMessage({ id, request }); } catch {
        fail(new Error('On-device analysis could not receive the captured image. Retake the photo.'));
      }
    });
  }
  return { analyze, dispose };
}
