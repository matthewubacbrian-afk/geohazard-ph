import { describe, expect, it, vi } from 'vitest';
import { createBrowserSceneAnalyzer } from '../src/services/browserSceneAnalysis';

function fakeWorker() {
  return { postMessage: vi.fn(), terminate: vi.fn(), onmessage: null, onerror: null } as unknown as Worker;
}
describe('device-only scene analysis lifecycle', () => {
  it('sends pictures only to a local worker, reuses it, and does not call an HTTP API', async () => {
    const worker = fakeWorker(), makeWorker = vi.fn(() => worker), fetchSpy = vi.spyOn(globalThis, 'fetch');
    const analyzer = createBrowserSceneAnalyzer(makeWorker);
    const promise = analyzer.analyze({ image_base64: 'private-photo', mime_type: 'image/jpeg' }, new AbortController().signal);
    const payload = vi.mocked(worker.postMessage).mock.calls[0][0];
    worker.onmessage?.call(worker, new MessageEvent('message', { data: { id: payload.id, type: 'result', result: { visual_cues: [] } } }));
    await expect(promise).resolves.toEqual({ visual_cues: [] });
    const repeat = analyzer.analyze({ image_base64: 'second-photo', mime_type: 'image/jpeg' }, new AbortController().signal);
    const next = vi.mocked(worker.postMessage).mock.calls[1][0];
    worker.onmessage?.call(worker, new MessageEvent('message', { data: { id: next.id, type: 'result', result: { visual_cues: [] } } }));
    await repeat;
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(makeWorker).toHaveBeenCalledTimes(1);
    analyzer.dispose();
    expect(worker.terminate).toHaveBeenCalled();
    fetchSpy.mockRestore();
  });
  it('terminates computation on cancellation and ignores late replies', async () => {
    const worker = fakeWorker(), controller = new AbortController();
    const analyzer = createBrowserSceneAnalyzer(() => worker);
    const result = analyzer.analyze({ image_base64: 'photo', mime_type: 'image/jpeg' }, controller.signal);
    controller.abort();
    await expect(result).rejects.toMatchObject({ name: 'AbortError' });
    expect(worker.terminate).toHaveBeenCalledTimes(1);
  });
  it('surfaces worker failures safely and releases the failed worker', async () => {
    const worker = fakeWorker();
    const analyzer = createBrowserSceneAnalyzer(() => worker);
    const result = analyzer.analyze({ image_base64: 'photo', mime_type: 'image/jpeg' }, new AbortController().signal);
    worker.onerror?.call(worker, new ErrorEvent('error', { message: 'private internals' }));
    await expect(result).rejects.toThrow(/on-device analysis/i);
    expect(worker.terminate).toHaveBeenCalled();
  });
  it('does not start a worker for an already cancelled request', async () => {
    const makeWorker = vi.fn(fakeWorker), controller = new AbortController();
    controller.abort();
    await expect(createBrowserSceneAnalyzer(makeWorker).analyze({ image_base64: 'photo', mime_type: 'image/jpeg' }, controller.signal))
      .rejects.toMatchObject({ name: 'AbortError' });
    expect(makeWorker).not.toHaveBeenCalled();
  });
  it('preserves the blur warning code for the existing continue/retake choices', async () => {
    const worker = fakeWorker(), analyzer = createBrowserSceneAnalyzer(() => worker);
    const result = analyzer.analyze({ image_base64: 'photo', mime_type: 'image/jpeg' }, new AbortController().signal);
    const payload = vi.mocked(worker.postMessage).mock.calls[0][0];
    worker.onmessage?.call(worker, new MessageEvent('message', { data: { id: payload.id, type: 'error', code: 'scene_image_quality_warning' } }));
    await expect(result).rejects.toMatchObject({ code: 'scene_image_quality_warning' });
    expect(worker.terminate).toHaveBeenCalled();
  });
});
