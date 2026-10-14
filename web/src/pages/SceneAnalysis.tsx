import { useEffect, useRef, useState } from 'react';
import { analyzeScene as requestSceneAnalysis } from '../api/sceneAnalysis';
import { API_BASE_URL } from '../api/client';
import type { SceneAnalysisRequest, SceneAnalysisResponse, SceneCapture } from '../types/sceneAnalysis';
import styles from './SceneAnalysis.module.css';

type SceneAnalysisProps = {
  onExit: () => void;
  analyze?: (request: SceneAnalysisRequest, signal: AbortSignal) => Promise<SceneAnalysisResponse>;
  initialCapture?: SceneCapture;
};

const DISCLAIMER = 'Visual cue demonstrator only. This is not a safety assessment or a production-ready emergency decision tool. It does not give emergency instructions, identify official shelters, or predict earthquakes. Verify conditions and follow official emergency guidance.';
const MAX_IMAGE_BYTES = 4 * 1024 * 1024;
const MAX_IMAGE_EDGE = 1600;
const JPEG_QUALITIES = [0.82, 0.68, 0.54, 0.4];
const SIZE_REDUCTION_STEPS = [1, 0.8, 0.64, 0.512];

export default function SceneAnalysis({
  onExit,
  analyze = (request, signal) => requestSceneAnalysis(API_BASE_URL, request, signal),
  initialCapture,
}: SceneAnalysisProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const cameraOpeningRef = useRef(false);
  const zoomOperationRef = useRef(0);
  const controllerRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);
  const [capture, setCapture] = useState<SceneCapture | null>(initialCapture ?? null);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraBusy, setCameraBusy] = useState(false);
  const [facingMode, setFacingMode] = useState<'environment' | 'user'>('environment');
  const [mirrorPreview, setMirrorPreview] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [zoomBusy, setZoomBusy] = useState(false);
  const [nativeZoomMax, setNativeZoomMax] = useState<number | null>(null);
  const [digitalZoom, setDigitalZoom] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<SceneAnalysisResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [qualityWarning, setQualityWarning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedRank, setSelectedRank] = useState(1);

  function stopCamera() {
    zoomOperationRef.current += 1;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setCameraActive(false);
    setZoom(1);
    setNativeZoomMax(null);
    setDigitalZoom(false);
    setZoomBusy(false);
  }

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      controllerRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    if (!cameraActive || !videoRef.current || !streamRef.current) return;
    videoRef.current.srcObject = streamRef.current;
    try {
      const playback = videoRef.current.play();
      if (playback && typeof playback.catch === 'function') void playback.catch(() => undefined);
    } catch {
      // The muted autoplay attribute still lets browsers start the stream where policy permits.
    }
  }, [cameraActive]);

  async function startCamera(nextFacing: 'environment' | 'user') {
    if (cameraOpeningRef.current || streamRef.current) return;
    cameraOpeningRef.current = true;
    setCameraBusy(true);
    setCameraError(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError('Camera access is not available in this browser or page context.');
      cameraOpeningRef.current = false;
      setCameraBusy(false);
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: nextFacing }, audio: false });
      if (!mountedRef.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      const track = stream.getVideoTracks?.()[0] ?? stream.getTracks().find((item) => item.kind === 'video');
      let supportedZoom: { min: number; max: number } | undefined;
      try {
        supportedZoom = (track?.getCapabilities?.() as (MediaTrackCapabilities & { zoom?: { min: number; max: number } }) | undefined)?.zoom;
      } catch {
        supportedZoom = undefined;
      }
      streamRef.current = stream;
      setFacingMode(nextFacing);
      setZoom(1);
      setNativeZoomMax(supportedZoom && supportedZoom.max > 1 ? supportedZoom.max : null);
      setDigitalZoom(!supportedZoom || supportedZoom.max <= 1);
      setCameraActive(true);
    } catch {
      if (mountedRef.current) {
        setCameraError('Camera permission was denied or the camera is unavailable. Check browser permissions and try again.');
      }
    } finally {
      cameraOpeningRef.current = false;
      if (mountedRef.current) setCameraBusy(false);
    }
  }

  function openCamera() {
    void startCamera(facingMode);
  }

  async function switchCamera(nextFacing: 'environment' | 'user') {
    if (nextFacing === facingMode || cameraOpeningRef.current) return;
    stopCamera();
    setCameraBusy(true);
    setFacingMode(nextFacing);
    setZoom(1);
    setNativeZoomMax(null);
    setDigitalZoom(false);
    await startCamera(nextFacing);
  }

  async function changeZoom(value: number) {
    const nextZoom = Math.min(nativeZoomMax ?? 3, Math.max(1, value));
    setZoom(nextZoom);
    const activeStream = streamRef.current;
    const track = activeStream?.getVideoTracks?.()[0] ?? activeStream?.getTracks().find((item) => item.kind === 'video');
    if (!track || digitalZoom) return;
    const zoomOperation = ++zoomOperationRef.current;
    setZoomBusy(true);
    try {
      await track.applyConstraints({ advanced: [{ zoom: nextZoom } as unknown as MediaTrackConstraintSet] });
    } catch {
      if (streamRef.current === activeStream) {
        setDigitalZoom(true);
        setNativeZoomMax(null);
      }
    } finally {
      if (mountedRef.current && zoomOperationRef.current === zoomOperation) setZoomBusy(false);
    }
  }

  function capturePhoto() {
    const video = videoRef.current;
    if (!video || video.videoWidth <= 0 || video.videoHeight <= 0) {
      setCameraError('The camera image is not ready yet. Please wait and try again.');
      return;
    }
    const canvas = document.createElement('canvas');
    const initialScale = Math.min(1, MAX_IMAGE_EDGE / Math.max(video.videoWidth, video.videoHeight));
    let compressedCapture: SceneCapture | null = null;
    let captureError: string | null = null;
    for (const reduction of SIZE_REDUCTION_STEPS) {
      canvas.width = Math.max(1, Math.round(video.videoWidth * initialScale * reduction));
      canvas.height = Math.max(1, Math.round(video.videoHeight * initialScale * reduction));
      const context = canvas.getContext('2d');
      if (!context) {
        captureError = 'The captured image could not be prepared in this browser.';
        break;
      }
      if (digitalZoom && zoom > 1) {
        const sourceWidth = video.videoWidth / zoom;
        const sourceHeight = video.videoHeight / zoom;
        context.drawImage(video, (video.videoWidth - sourceWidth) / 2, (video.videoHeight - sourceHeight) / 2,
          sourceWidth, sourceHeight, 0, 0, canvas.width, canvas.height);
      } else {
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
      }
      for (const quality of JPEG_QUALITIES) {
        const dataUrl = canvas.toDataURL('image/jpeg', quality);
        if (!dataUrl.startsWith('data:image/jpeg;base64,')) {
          captureError = 'This browser could not prepare the image as JPEG.';
          break;
        }
        const imageBase64 = dataUrl.slice(dataUrl.indexOf(',') + 1);
        const imageBytes = Math.floor(imageBase64.length * 3 / 4) -
          (imageBase64.endsWith('==') ? 2 : imageBase64.endsWith('=') ? 1 : 0);
        if (imageBase64 && imageBytes <= MAX_IMAGE_BYTES) {
          compressedCapture = { previewUrl: dataUrl, imageBase64 };
          break;
        }
      }
      if (compressedCapture || captureError) break;
    }
    stopCamera();
    if (!compressedCapture) {
      setCameraError(captureError ?? 'The image could not be compressed below 4 MiB. Try a simpler or farther-away view.');
      return;
    }
    setCapture(compressedCapture);
    setAnalysis(null);
    setAnalysisError(null);
    setQualityWarning(false);
    setSelectedRank(1);
  }

  function clearCapture() {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setLoading(false);
    setCapture(null);
    setAnalysis(null);
    setAnalysisError(null);
    setQualityWarning(false);
    setCameraError(null);
  }

  async function submitAnalysis(acceptQualityWarning = false) {
    if (!capture) return;
    const controller = new AbortController();
    controllerRef.current?.abort();
    controllerRef.current = controller;
    setLoading(true);
    setAnalysisError(null);
    setQualityWarning(false);
    try {
      const result = await analyze(
        { image_base64: capture.imageBase64, mime_type: 'image/jpeg', accept_quality_warning: acceptQualityWarning },
        controller.signal,
      );
      if (!controller.signal.aborted) setAnalysis(result);
    } catch (error) {
      if (!controller.signal.aborted) {
        if (error instanceof Error && 'code' in error && error.code === 'scene_image_quality_warning') {
          setQualityWarning(true);
        } else {
          setAnalysisError(error instanceof Error ? error.message : 'Scene analysis failed. Please try again.');
        }
      }
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }

  const selectedCandidate = analysis?.candidate_regions.find((candidate) => candidate.rank === selectedRank);

  return (
    <main className={styles.page}>
      <div className={styles.content}>
        <header className={styles.heading}>
          <button type="button" className={styles.backButton} aria-label="Back" onClick={onExit}><span aria-hidden="true">←</span> Dashboard</button>
          <div className={styles.headingCopy}>
            <p className={styles.eyebrow}>FIELD TOOL · EPIC 7</p>
            <h1>Camera scene review</h1>
            <p>Review a captured indoor or outdoor scene for visible floor or ground candidates and recognized objects.</p>
          </div>
        </header>

        <div className={styles.safetyNotes}>
          <p className={styles.notice} role="note"><strong>For situational awareness</strong><span>{DISCLAIMER}</span></p>
          <p className={styles.privacy}><span aria-hidden="true">▣</span> The image is sent to this project’s Python service for temporary analysis. The captured preview stays on this screen and is cleared when you retake or leave.</p>
        </div>
        {cameraError && <p className={styles.error} role="alert">{cameraError}</p>}

        <div className={styles.workspace}>
          <section className={styles.stage} aria-label="Scene capture">
            <div className={styles.stageHeader}>
              <div><p className={styles.eyebrow}>01 / CAPTURE</p><h2>{cameraActive ? 'Live camera' : capture ? 'Captured scene' : 'Ready when you are'}</h2></div>
              {cameraActive && <span className={styles.liveBadge}><span /> LIVE</span>}
            </div>
            <div className={styles.viewfinder}>
              {cameraActive && <video
                className={`${styles.video} ${mirrorPreview ? styles.mirrored : ''}`}
                style={{ '--digital-zoom': digitalZoom ? zoom : 1 } as React.CSSProperties}
                ref={videoRef} autoPlay muted playsInline aria-label="Camera preview"
              />}
              {!cameraActive && capture && <div className={styles.previewFrame}>
                <img className={styles.preview} src={capture.previewUrl} alt="Captured scene preview" />
                {analysis && selectedCandidate && <svg className={styles.overlay} viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label={`Candidate region ${selectedCandidate.rank}`}>
                  {analysis.candidate_regions.map((candidate) => <polygon
                    key={candidate.rank}
                    className={`${styles.candidateShape} ${candidate.rank === selectedRank ? styles.candidateShapeSelected : ''}`}
                    points={candidate.polygon.map((point) => `${point.x * 100},${point.y * 100}`).join(' ')}
                  />)}
                </svg>}
              </div>}
              {!cameraActive && !capture && <div className={styles.emptyStage}>
                <span className={styles.cameraGlyph} aria-hidden="true">⌖</span>
                <strong>Camera preview will appear here</strong>
                <span>Frame the area you want to review. Keep the scene well lit and steady.</span>
              </div>}
              {cameraBusy && <div className={styles.cameraLoading} role="status">Connecting to camera…</div>}
            </div>
            <div className={styles.stageActions}>
              {cameraActive && <>
                <button type="button" className={styles.primaryButton} onClick={capturePhoto} disabled={zoomBusy}>Capture photo</button>
                <button type="button" className={styles.secondaryButton} onClick={stopCamera}>Close camera</button>
              </>}
              {capture && <>
                <button type="button" className={styles.primaryButton} onClick={() => void submitAnalysis()} disabled={loading}>
                  {loading ? 'Analyzing…' : analysis ? 'Analyze again' : 'Analyze image'}
                </button>
                <button type="button" className={styles.secondaryButton} onClick={clearCapture}>Retake photo</button>
              </>}
            </div>
          </section>

          <aside className={styles.controlPanel} aria-label="Camera settings and guidance">
            <section className={styles.settingsCard} aria-labelledby="camera-settings-title">
              <p className={styles.eyebrow}>02 / CAMERA SETUP</p>
              <h2 id="camera-settings-title">Camera settings</h2>
              <label className={styles.fieldLabel} htmlFor="camera-facing">Camera</label>
              <select id="camera-facing" className={styles.select} value={facingMode} disabled={cameraBusy}
                onChange={(event) => {
                  const next = event.target.value as 'environment' | 'user';
                  if (cameraActive) void switchCamera(next);
                  else setFacingMode(next);
                }}>
                <option value="environment">Back camera</option>
                <option value="user">Front camera</option>
              </select>
              {cameraActive ? <>
                <label className={styles.toggleRow}>
                  <span><strong>Mirror preview</strong><small>Flips the on-screen preview only</small></span>
                  <input type="checkbox" checked={mirrorPreview} onChange={(event) => setMirrorPreview(event.target.checked)} />
                </label>
                <div className={styles.zoomControl}>
                  <div className={styles.zoomLabel}><label htmlFor="camera-zoom">Zoom</label><output htmlFor="camera-zoom">{zoom.toFixed(1)}×</output></div>
                  <input id="camera-zoom" aria-label="Camera zoom" type="range" min="1" max={nativeZoomMax ?? 3} step="0.1" value={zoom} disabled={zoomBusy}
                    onChange={(event) => void changeZoom(Number(event.target.value))} />
                  <div className={styles.zoomScale}><span>1×</span><span>{(nativeZoomMax ?? 3).toFixed(1)}×</span></div>
                  <small>{zoomBusy ? 'Adjusting camera zoom…' : digitalZoom ? 'Digital zoom · included in captured image' : 'Device camera zoom'}</small>
                </div>
              </> : <p className={styles.mutedCopy}>Choose which camera to use. You can change it while the camera is open.</p>}
              {!cameraActive && !capture && <button type="button" className={styles.primaryButton} onClick={openCamera} disabled={cameraBusy}>
                {cameraBusy ? 'Opening camera…' : 'Open camera'}
              </button>}
            </section>
            <section className={styles.guideCard} aria-labelledby="capture-guide-title">
              <p className={styles.eyebrow}>QUICK GUIDE</p>
              <h2 id="capture-guide-title">Get a clearer review</h2>
              <ol><li>Hold the camera steady and include the full area.</li><li>Use good lighting and avoid blur or obstructions.</li><li>Review the capture before sending it for analysis.</li></ol>
              <p>Scene Review identifies visual cues only. It cannot determine whether a place is safe.</p>
            </section>
          </aside>
        </div>

        {loading && <p role="status">Analyzing the image in temporary memory…</p>}
        {analysisError && <div className={styles.notice}>
          <p className={styles.error} role="alert">{analysisError}</p>
          <button type="button" className={styles.button} onClick={() => void submitAnalysis()}>Retry analysis</button>
        </div>}
        {qualityWarning && <div className={styles.notice} role="group" aria-label="Image quality choices">
          <p role="alert">This photo may be blurry. Retake it for a clearer view. If you continue, image cues may be missed or incomplete.</p>
          <button type="button" className={styles.button} onClick={() => void submitAnalysis(true)} disabled={loading}>Continue anyway</button>
          <button type="button" className={styles.button} onClick={clearCapture} disabled={loading}>Retake blurry photo</button>
        </div>}
        {analysis && <section aria-labelledby="evidence-title">
          <h2 id="evidence-title">Evidence checklist</h2>
          {analysis.candidate_regions.length === 0 ? <p>No clear open-area candidate was identified in this image.</p> : <>
            <p>Visible candidate regions are ranked by image cues for review. The review-order heuristic is: (relative area × 0.50) + (shape compactness × 0.30) + (model confidence × 0.20), where relative area = min(candidate visible pixel area ÷ largest candidate visible pixel area, 1). The score is a heuristic review-order value, not a percent or probability of safety.</p>
            <ul className={styles.candidateList} aria-label="Candidate areas">
              {analysis.candidate_regions.map((candidate) => <li key={candidate.rank}>
                <button type="button" className={`${styles.candidate} ${candidate.rank === selectedRank ? styles.selected : ''}`}
                  aria-pressed={candidate.rank === selectedRank} aria-label={`Candidate region ${candidate.rank}: ${candidate.surface_class}`}
                  onClick={() => setSelectedRank(candidate.rank)}>
                  Candidate {candidate.rank} · {candidate.surface_class.replace(/-/g, ' ')} · ranking heuristic: {candidate.ranking_score.toFixed(2)} (0.00–1.00)
                </button>
                <ul className={styles.checklist} aria-label={`Evidence for candidate ${candidate.rank}`}>
                  <li>Visible area: {Math.round(candidate.area_fraction * 100)}% of the image.</li>
                  <li>Shape compactness: {Math.round(candidate.compactness * 100)}%.</li>
                  <li>Model confidence: {Math.round(candidate.model_confidence * 100)}%.</li>
                </ul>
              </li>)}
            </ul>
          </>}
          <ul className={styles.checklist}>
            <li>{analysis.candidate_regions.length ? `${analysis.candidate_regions.length} visible floor or ground candidate region(s) detected.` : 'No clear floor or ground candidate region was detected.'}</li>
            {analysis.visual_cues.length ? analysis.visual_cues.map((cue) => <li key={cue.class_name}>Recognized visual cue: {cue.class_name.replace(/-/g, ' ')} ({Math.round(cue.model_confidence * 100)}% model confidence).</li>) : <li>No listed object cues were recognized.</li>}
          </ul>
          <p className={styles.notice}>{analysis.limitations.join(' ')}</p>
        </section>}
      </div>
    </main>
  );
}
