import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { analyzeScene } from '../src/api/sceneAnalysis';
import SceneAnalysis from '../src/pages/SceneAnalysis';
import type { SceneAnalysisResponse } from '../src/types/sceneAnalysis';

const responsePayload: SceneAnalysisResponse = {
  model_version: 'pinned-model',
  result_status: 'candidates_found',
  candidate_regions: [{
    rank: 1,
    surface_class: 'floor-tile',
    polygon: [{ x: 0.1, y: 0.1 }, { x: 0.9, y: 0.1 }, { x: 0.9, y: 0.9 }, { x: 0.1, y: 0.9 }, { x: 0.1, y: 0.1 }],
    area_fraction: 0.2,
    compactness: 0.8,
    model_confidence: 0.9,
    ranking_score: 0.7,
  }],
  visual_cues: [{ class_name: 'chair', model_confidence: 0.8 }],
  limitations: [
    'Visual scene cues only; this result does not determine whether any area is safe.',
    'A single image cannot assess structural stability, hidden or changing hazards, or whether a route is accessible.',
  ],
};

describe('scene analysis API', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('posts a JPEG to the shared scene endpoint and returns the wire response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(responsePayload), { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);

    await expect(analyzeScene('https://api.example/api/v1', {
      image_base64: 'ZmFrZQ==', mime_type: 'image/jpeg',
    })).resolves.toEqual(responsePayload);
    expect(fetchMock).toHaveBeenCalledWith('https://api.example/api/v1/scene-analyses', expect.objectContaining({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_base64: 'ZmFrZQ==', mime_type: 'image/jpeg' }),
    }));
  });

  it.each([413, 422, 503])('maps HTTP %s to a safe typed error without exposing image data', async (status) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      error: { code: 'scene_unavailable', message: 'Scene analysis is unavailable.' },
    }), { status })));
    const log = vi.spyOn(console, 'error');

    await expect(analyzeScene('/api/v1', { image_base64: 'secret-photo', mime_type: 'image/jpeg' }))
      .rejects.toMatchObject({ status });
    expect(log).not.toHaveBeenCalled();
  });

  it('rejects malformed API responses', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 200 })));
    await expect(analyzeScene('/api/v1', { image_base64: 'ZmFrZQ==', mime_type: 'image/jpeg' }))
      .rejects.toThrow(/scene analysis response was invalid/i);
  });
});

describe('scene review capture screen', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('does not request camera permission until the user starts capture', () => {
    const getUserMedia = vi.fn();
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia } });
    render(<SceneAnalysis onExit={vi.fn()} />);
    expect(getUserMedia).not.toHaveBeenCalled();
    expect(screen.getByText(/visual cues only—not a safety assessment/i)).toBeInTheDocument();
    expect(screen.getByText(/sent to this project’s python service for temporary analysis/i)).toBeInTheDocument();
  });

  it('opens only one camera stream when the user clicks twice rapidly', async () => {
    let resolveStream: ((stream: MediaStream) => void) | undefined;
    const stop = vi.fn();
    const stream = { getTracks: () => [{ stop }] } as unknown as MediaStream;
    const getUserMedia = vi.fn(() => new Promise<MediaStream>((resolve) => { resolveStream = resolve; }));
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia } });
    vi.spyOn(HTMLVideoElement.prototype, 'play').mockResolvedValue();
    const { unmount } = render(<SceneAnalysis onExit={vi.fn()} />);
    const openButton = screen.getByRole('button', { name: /open camera/i });

    fireEvent.click(openButton);
    fireEvent.click(openButton);
    expect(getUserMedia).toHaveBeenCalledOnce();
    resolveStream?.(stream);
    await waitFor(() => expect(screen.getByRole('button', { name: /capture photo/i })).toBeInTheDocument());
    unmount();
    expect(stop).toHaveBeenCalledOnce();
  });
  it('reports unsupported and denied camera states without claiming safety', async () => {
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia: vi.fn().mockRejectedValue(new Error('denied')) } });
    render(<SceneAnalysis onExit={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /open camera/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/camera permission/i);
  });

  it('stops every active camera track when the capture screen exits', async () => {
    const stop = vi.fn();
    vi.spyOn(HTMLVideoElement.prototype, 'play').mockResolvedValue();
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia: vi.fn().mockResolvedValue({ getTracks: () => [{ stop }] }) } });
    const { unmount } = render(<SceneAnalysis onExit={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /open camera/i }));
    await waitFor(() => expect(screen.getByRole('button', { name: /capture photo/i })).toBeInTheDocument());
    unmount();
    expect(stop).toHaveBeenCalledOnce();
  });

  it('stops camera tracks after capture and shows candidate polygon with evidence checklist', async () => {
    const stop = vi.fn();
    const stream = { getTracks: () => [{ stop }] };
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia: vi.fn().mockResolvedValue(stream) } });
    const toDataURL = vi.fn().mockReturnValue('data:image/jpeg;base64,ZmFrZQ==');
    const drawImage = vi.fn();
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({ drawImage } as unknown as CanvasRenderingContext2D);
    vi.spyOn(HTMLCanvasElement.prototype, 'toDataURL').mockImplementation(toDataURL);
    vi.spyOn(HTMLVideoElement.prototype, 'play').mockResolvedValue();
    vi.spyOn(HTMLVideoElement.prototype, 'videoWidth', 'get').mockReturnValue(2400);
    vi.spyOn(HTMLVideoElement.prototype, 'videoHeight', 'get').mockReturnValue(1800);

    const analyze = vi.fn().mockResolvedValue(responsePayload);
    render(<SceneAnalysis onExit={vi.fn()} analyze={analyze} />);
    fireEvent.click(screen.getByRole('button', { name: /open camera/i }));
    await waitFor(() => expect(screen.getByRole('button', { name: /capture photo/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /capture photo/i }));
    expect(stop).toHaveBeenCalled();
    expect(drawImage).toHaveBeenCalledWith(expect.any(HTMLVideoElement), 0, 0, 1600, 1200);
    expect(await screen.findByRole('img', { name: /captured scene preview/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /analyze image/i }));
    const overlay = await screen.findByRole('img', { name: /candidate region 1/i });
    expect(overlay.querySelector('polygon')).toHaveAttribute('points', '10,10 90,10 90,90 10,90 10,10');
    expect(screen.getByText(/chair/i)).toBeInTheDocument();
    expect(screen.getByRole('list', { name: 'Evidence for candidate 1' })).toHaveTextContent(/visible area: 20%/i);
    expect(screen.getByRole('list', { name: 'Evidence for candidate 1' })).toHaveTextContent(/shape compactness: 80%/i);
    expect(screen.getByRole('list', { name: 'Evidence for candidate 1' })).toHaveTextContent(/model confidence: 90%/i);
    expect(screen.getByRole('button', { name: /candidate region 1/i })).toHaveTextContent(/ranking heuristic: 0\.70/i);
    expect(screen.getByText(/relative area × 0\.50.*shape compactness × 0\.30.*model confidence × 0\.20/i)).toBeInTheDocument();
    expect(screen.queryByText(/70% cue score/i)).not.toBeInTheDocument();
    expect(screen.getByText(/visual cues only—not a safety assessment/i)).toBeInTheDocument();
    expect(analyze).toHaveBeenCalledWith(expect.objectContaining({ image_base64: 'ZmFrZQ==', mime_type: 'image/jpeg' }), expect.any(AbortSignal));
  });

  it('re-encodes a large capture at lower quality before rejecting it', async () => {
    const stop = vi.fn();
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia: vi.fn().mockResolvedValue({ getTracks: () => [{ stop }] }) } });
    const toDataURL = vi.fn()
      .mockReturnValueOnce(`data:image/jpeg;base64,${'A'.repeat(5_600_000)}`)
      .mockReturnValueOnce('data:image/jpeg;base64,ZmFrZQ==');
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({ drawImage: vi.fn() } as unknown as CanvasRenderingContext2D);
    vi.spyOn(HTMLCanvasElement.prototype, 'toDataURL').mockImplementation(toDataURL);
    vi.spyOn(HTMLVideoElement.prototype, 'play').mockResolvedValue();
    vi.spyOn(HTMLVideoElement.prototype, 'videoWidth', 'get').mockReturnValue(800);
    vi.spyOn(HTMLVideoElement.prototype, 'videoHeight', 'get').mockReturnValue(600);
    render(<SceneAnalysis onExit={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /open camera/i }));
    await waitFor(() => expect(screen.getByRole('button', { name: /capture photo/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /capture photo/i }));
    expect(toDataURL).toHaveBeenCalledTimes(2);
    expect(toDataURL.mock.calls[1][1]).toBeLessThan(toDataURL.mock.calls[0][1] as number);
    expect(await screen.findByRole('img', { name: /captured scene preview/i })).toHaveAttribute('src', 'data:image/jpeg;base64,ZmFrZQ==');
    expect(stop).toHaveBeenCalled();
  });

  it('renders an explicit empty result when no candidate regions are returned', async () => {
    const analyze = vi.fn().mockResolvedValue({ ...responsePayload, candidate_regions: [], result_status: 'no_clear_candidate', visual_cues: [] });
    render(<SceneAnalysis onExit={vi.fn()} initialCapture={{ previewUrl: 'data:image/jpeg;base64,ZmFrZQ==', imageBase64: 'ZmFrZQ==' }} analyze={analyze} />);
    fireEvent.click(screen.getByRole('button', { name: /analyze image/i }));
    expect(await screen.findByText(/no clear open-area candidate was identified/i)).toBeInTheDocument();
  });

  it('shows a retry state after an analysis error', async () => {
    const analyze = vi.fn().mockRejectedValueOnce(new Error('Scene analysis is temporarily unavailable. Please try again later.'))
      .mockResolvedValueOnce(responsePayload);
    render(<SceneAnalysis onExit={vi.fn()} initialCapture={{ previewUrl: 'data:image/jpeg;base64,ZmFrZQ==', imageBase64: 'ZmFrZQ==' }} analyze={analyze} />);
    fireEvent.click(screen.getByRole('button', { name: /analyze image/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/temporarily unavailable/i);
    fireEvent.click(screen.getByRole('button', { name: /retry analysis/i }));
    expect(await screen.findByRole('heading', { name: /evidence checklist/i })).toBeInTheDocument();
  });

  it('aborts a pending analysis and clears its preview when retaking', async () => {
    let pendingSignal: AbortSignal | undefined;
    const analyze = vi.fn((_request: { image_base64: string; mime_type: 'image/jpeg' }, signal: AbortSignal) => {
      pendingSignal = signal;
      return new Promise<SceneAnalysisResponse>(() => undefined);
    });
    render(<SceneAnalysis onExit={vi.fn()} initialCapture={{ previewUrl: 'data:image/jpeg;base64,ZmFrZQ==', imageBase64: 'ZmFrZQ==' }} analyze={analyze} />);
    fireEvent.click(screen.getByRole('button', { name: /analyze image/i }));
    await waitFor(() => expect(pendingSignal).toBeDefined());
    fireEvent.click(screen.getByRole('button', { name: /retake photo/i }));
    expect(pendingSignal?.aborted).toBe(true);
    expect(screen.queryByRole('img', { name: /captured scene preview/i })).not.toBeInTheDocument();
  });

  it('aborts analysis and releases the capture when the parent exits the route', async () => {
    let pendingSignal: AbortSignal | undefined;
    const analyze = vi.fn((_request: { image_base64: string; mime_type: 'image/jpeg' }, signal: AbortSignal) => {
      pendingSignal = signal;
      return new Promise<SceneAnalysisResponse>(() => undefined);
    });
    function RouteHarness() {
      const [active, setActive] = useState(true);
      return active
        ? <SceneAnalysis onExit={() => setActive(false)} initialCapture={{ previewUrl: 'data:image/jpeg;base64,ZmFrZQ==', imageBase64: 'ZmFrZQ==' }} analyze={analyze} />
        : <p>Dashboard route</p>;
    }
    render(<RouteHarness />);
    fireEvent.click(screen.getByRole('button', { name: /analyze image/i }));
    await waitFor(() => expect(pendingSignal).toBeDefined());
    fireEvent.click(screen.getByRole('button', { name: 'Back' }));
    expect(await screen.findByText('Dashboard route')).toBeInTheDocument();
    expect(pendingSignal?.aborted).toBe(true);
    expect(screen.queryByRole('img', { name: /captured scene preview/i })).not.toBeInTheDocument();
  });
});
