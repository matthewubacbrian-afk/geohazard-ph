import { SCENE_MODEL, SCENE_REVISION, sceneFromMasks, type SceneMask } from './sceneMasks';
import type { SceneAnalysisRequest } from '../types/sceneAnalysis';

// Versioned public files only. No inference provider, account token, or photo upload.
const RUNTIME_URL = 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1/dist/transformers.min.js';
const WASM_URL = 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.22.0-dev.20250409-89f8206ba4/dist/';
type RawImage = {
  width: number; height: number; channels: number; data: Uint8Array | Uint8ClampedArray;
  rgb(): RawImage; resize(width: number, height: number): Promise<RawImage>;
};
type Segmenter = {
  (image: RawImage): Promise<SceneMask[]>;
  processor: { image_processor: { size: { shortest_edge: number; longest_edge: number } } };
};
type Runtime = {
  env: { allowLocalModels: boolean; useBrowserCache: boolean;
    backends: { onnx: { wasm: { numThreads: number; proxy: boolean; wasmPaths: string } } } };
  RawImage: { fromURL(url: string): Promise<RawImage> };
  pipeline(task: string, model: string, options: Record<string, unknown>): Promise<Segmenter>;
};
let runtime: Promise<Runtime> | null = null;
let model: Promise<Segmenter> | null = null;

function sharpness(image: RawImage): number {
  const gray = (x: number, y: number) => {
    const i = (y * image.width + x) * image.channels;
    return image.data[i] * 0.299 + image.data[i + 1] * 0.587 + image.data[i + 2] * 0.114;
  };
  let sum = 0, squared = 0, count = 0;
  for (let y = 1; y + 1 < image.height; y++) for (let x = 1; x + 1 < image.width; x++) {
    const value = gray(x - 1, y) + gray(x + 1, y) + gray(x, y - 1) + gray(x, y + 1) - 4 * gray(x, y);
    sum += value; squared += value * value; count++;
  }
  return count ? squared / count - (sum / count) ** 2 : 0;
}

self.onmessage = async ({ data }: MessageEvent<{ id: number; request: SceneAnalysisRequest }>) => {
  const { id, request } = data;
  const progress = (phase: string) => self.postMessage({ id, type: 'progress', phase });
  let stage = 'invalid_scene_image';
  try {
    if (request.mime_type !== 'image/jpeg' || !request.image_base64.startsWith('/9j/')
      || request.image_base64.length > 5_592_408) throw new Error('Invalid JPEG');
    stage = 'scene_analysis_unavailable';
    progress('decoding');
    runtime ??= import(/* @vite-ignore */ RUNTIME_URL) as Promise<Runtime>;
    const library = await runtime;
    library.env.allowLocalModels = false;
    library.env.useBrowserCache = true;
    library.env.backends.onnx.wasm.numThreads = 1;
    library.env.backends.onnx.wasm.proxy = false;
    library.env.backends.onnx.wasm.wasmPaths = WASM_URL;
    stage = 'invalid_scene_image';
    let image = (await library.RawImage.fromURL(`data:image/jpeg;base64,${request.image_base64}`)).rgb();
    if (image.width > 1600 || image.height > 1600) throw new Error('Image too large');
    const scale = Math.min(1, 512 / Math.max(image.width, image.height));
    if (scale < 1) image = await image.resize(Math.max(1, Math.round(image.width * scale)), Math.max(1, Math.round(image.height * scale)));
    if (!request.accept_quality_warning && sharpness(image) < 400) {
      self.postMessage({ id, type: 'error', code: 'scene_image_quality_warning' }); return;
    }
    stage = 'scene_analysis_unavailable';
    progress('loading');
    model ??= library.pipeline('image-segmentation', SCENE_MODEL, {
      revision: SCENE_REVISION, dtype: 'q8', device: 'wasm',
    }).then((pipeline) => {
      // Bound device work. This is a distinct browser demonstrator configuration.
      pipeline.processor.image_processor.size = { shortest_edge: 384, longest_edge: 512 };
      return pipeline;
    });
    const segmenter = await model;
    progress('analyzing');
    const segments = await segmenter(image);
    self.postMessage({ id, type: 'result', result: sceneFromMasks(segments) });
  } catch {
    // Do not send exceptions, image data, or stack traces to the page/logs.
    self.postMessage({ id, type: 'error', code: stage });
  }
};
