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
  const controllerRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);
  const [capture, setCapture] = useState<SceneCapture | null>(initialCapture ?? null);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<SceneAnalysisResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [qualityWarning, setQualityWarning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedRank, setSelectedRank] = useState(1);

  function stopCamera() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setCameraActive(false);
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

  async function openCamera() {
    if (cameraOpeningRef.current || streamRef.current) return;
    cameraOpeningRef.current = true;
    setCameraError(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError('Camera access is not available in this browser or page context.');
      cameraOpeningRef.current = false;
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false });
      if (!mountedRef.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      streamRef.current = stream;
      setCameraActive(true);
    } catch {
      if (mountedRef.current) {
        setCameraError('Camera permission was denied or the camera is unavailable. Check browser permissions and try again.');
      }
    } finally {
      cameraOpeningRef.current = false;
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
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
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
          <button type="button" className={styles.button} onClick={onExit}>Back</button>
          <h1>Camera scene review</h1>
          <p>Review a captured indoor or outdoor scene for visible floor or ground candidates and recognized objects.</p>
        </header>

        <p className={styles.notice} role="note">{DISCLAIMER}</p>
        <p className={styles.privacy}>The image is sent to this project’s Python service for temporary analysis. The captured preview stays on this screen and is cleared when you retake or leave.</p>
        {cameraError && <p className={styles.error} role="alert">{cameraError}</p>}

        {cameraActive && <>
          <video className={styles.video} ref={videoRef} autoPlay muted playsInline aria-label="Camera preview" />
          <div className={styles.actions}>
            <button type="button" className={styles.button} onClick={capturePhoto}>Capture photo</button>
            <button type="button" className={styles.button} onClick={stopCamera}>Close camera</button>
          </div>
        </>}

        {!cameraActive && !capture && <div className={styles.actions}>
          <button type="button" className={styles.button} onClick={() => void openCamera()}>Open camera</button>
        </div>}

        {capture && <>
          <div className={styles.previewFrame}>
            <img className={styles.preview} src={capture.previewUrl} alt="Captured scene preview" />
            {analysis && selectedCandidate && <svg className={styles.overlay} viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label={`Candidate region ${selectedCandidate.rank}`}>
              {analysis.candidate_regions.map((candidate) => <polygon
                key={candidate.rank}
                className={`${styles.candidateShape} ${candidate.rank === selectedRank ? styles.candidateShapeSelected : ''}`}
                points={candidate.polygon.map((point) => `${point.x * 100},${point.y * 100}`).join(' ')}
              />)}
            </svg>}
          </div>
          <div className={styles.actions}>
            <button type="button" className={styles.button} onClick={() => void submitAnalysis()} disabled={loading}>
              {loading ? 'Analyzing…' : analysis ? 'Analyze again' : 'Analyze image'}
            </button>
            <button type="button" className={styles.button} onClick={clearCapture}>Retake photo</button>
          </div>
        </>}

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
