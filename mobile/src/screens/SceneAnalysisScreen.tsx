import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Image, Pressable, ScrollView, Text, View } from 'react-native';
import Svg, { Polygon } from 'react-native-svg';

import {
  analyzeScene, captureSceneImage, SCENE_ANALYSIS_CAVEAT,
  type SceneAnalysisError,
} from '../services/sceneAnalysis';
import { styles } from '../styles';
import type { SceneAnalysisResult } from '../types/sceneAnalysis';

type ScenePreview = { uri: string; width: number; height: number };

type Props = { apiBaseUrl: string; isActive: boolean };

export default function SceneAnalysisScreen({ apiBaseUrl, isActive }: Props) {
  const isMounted = useRef(true);
  const isActiveRef = useRef(isActive);
  const captureRevision = useRef(0);
  isActiveRef.current = isActive;
  const activeRequest = useRef<AbortController | null>(null);
  const [image, setImage] = useState<ScenePreview | null>(null);
  const [imageBase64, setImageBase64] = useState<string | null>(null);
  const [result, setResult] = useState<SceneAnalysisResult | null>(null);
  const [selectedRank, setSelectedRank] = useState(1);
  const [isCapturing, setIsCapturing] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
      activeRequest.current?.abort();
      activeRequest.current = null;
    };
  }, []);

  useEffect(() => {
    if (isActive) return;
    activeRequest.current?.abort();
    activeRequest.current = null;
    captureRevision.current += 1;
    setImage(null);
    setImageBase64(null);
    setResult(null);
    setSelectedRank(1);
    setError(null);
    setIsCapturing(false);
    setIsAnalyzing(false);
  }, [isActive]);

  async function capture(retake = false) {
    const revision = ++captureRevision.current;
    if (retake) {
      setImage(null);
      setImageBase64(null);
      setResult(null);
      setSelectedRank(1);
    }
    setError(null);
    setIsCapturing(true);
    const outcome = await captureSceneImage();
    if (!isMounted.current || !isActiveRef.current || revision !== captureRevision.current) return;
    setIsCapturing(false);
    if (outcome.status === 'error') setError(outcome.message);
    if (outcome.status === 'captured') {
      setImage({ uri: outcome.image.uri, width: outcome.image.width, height: outcome.image.height });
      setImageBase64(outcome.image.imageBase64);
      setResult(null);
    }
  }

  async function submitAnalysis() {
    if (!imageBase64) return;
    const controller = new AbortController();
    activeRequest.current = controller;
    setError(null);
    setIsAnalyzing(true);
    try {
      const nextResult = await analyzeScene(apiBaseUrl, imageBase64, controller.signal);
      if (!isMounted.current || !isActiveRef.current) return;
      setResult(nextResult);
      setImageBase64(null);
      setSelectedRank(1);
    } catch (reason) {
      if (controller.signal.aborted || !isMounted.current || !isActiveRef.current) return;
      setError((reason as SceneAnalysisError).message ?? 'Could not analyze this scene. Please try again.');
    } finally {
      if (activeRequest.current === controller) activeRequest.current = null;
      if (isMounted.current && isActiveRef.current) setIsAnalyzing(false);
    }
  }

  const selectedCandidate = result?.candidateRegions.find((candidate) => candidate.rank === selectedRank);
  const imageWidth = image?.width || 1;
  const imageHeight = image?.height || 1;

  if (!isActive) return null;

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Scene review</Text>
      <Text style={styles.body}>Capture a room or outdoor area to review visible floor or ground cues.</Text>
      <Text accessibilityRole="text" style={styles.notice}>{SCENE_ANALYSIS_CAVEAT}</Text>

      {!image ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Open camera to capture a scene"
          disabled={isCapturing}
          onPress={() => void capture()}
          style={styles.actionButton}
        >
          <Text style={styles.actionText}>{isCapturing ? 'Opening camera…' : 'Open camera'}</Text>
        </Pressable>
      ) : (
        <>
          <View style={styles.scenePreview}>
            <Image source={{ uri: image.uri }} resizeMode="contain" style={styles.sceneImage} />
            {selectedCandidate ? (
              <Svg pointerEvents="none" preserveAspectRatio="xMidYMid meet" style={styles.sceneOverlay} viewBox={`0 0 ${imageWidth} ${imageHeight}`}>
                <Polygon
                  fill="rgba(34, 197, 94, 0.24)"
                  points={selectedCandidate.polygon.map((point) => `${point.x * imageWidth},${point.y * imageHeight}`).join(' ')}
                  stroke="#16834a"
                  strokeWidth={Math.max(imageWidth, imageHeight) * 0.008}
                />
              </Svg>
            ) : null}
          </View>
          {!result ? (
            <>
              <Pressable accessibilityRole="button" disabled={isAnalyzing} onPress={() => void submitAnalysis()} style={styles.actionButton}>
                <Text style={styles.actionText}>{isAnalyzing ? 'Reviewing visual cues…' : 'Analyze captured scene'}</Text>
              </Pressable>
              {isAnalyzing ? <ActivityIndicator accessibilityLabel="Analyzing scene" style={{ marginTop: 12 }} /> : null}
            </>
          ) : (
            <>
              <Text style={styles.sectionTitle}>Evidence checklist</Text>
              <Text style={styles.body}>The items below are model-detected visual cues. They do not confirm site conditions.</Text>
              <Text style={styles.muted}>
                Candidate ordering combines relative visible area (50%), shape compactness (30%), and model class confidence (20%). The 0–1 weighted heuristic is a sorting cue, not a safety probability.
              </Text>
              {result.candidateRegions.length === 0 ? (
                <Text style={styles.notice}>No clear floor or ground candidate was identified. Try another view with more of the surface visible.</Text>
              ) : (
                <>
                  <Text style={styles.sectionTitle}>Candidate areas</Text>
                  {result.candidateRegions.map((candidate) => (
                    <Pressable
                      accessibilityRole="button"
                      accessibilityState={{ selected: selectedRank === candidate.rank }}
                      key={candidate.rank}
                      onPress={() => setSelectedRank(candidate.rank)}
                      style={[styles.candidateButton, selectedRank === candidate.rank && styles.candidateButtonSelected]}
                    >
                      <Text style={styles.candidateTitle}>Candidate {candidate.rank}: {candidate.surfaceClass}</Text>
                      <Text style={styles.candidateMetric}>Visible image area: {Math.round(candidate.areaFraction * 100)}%</Text>
                      <Text style={styles.candidateMetric}>Shape compactness: {candidate.compactness.toFixed(2)} / 1.00</Text>
                      <Text style={styles.candidateMetric}>Model class confidence: {candidate.modelConfidence.toFixed(2)} / 1.00 (not safety confidence)</Text>
                      <Text style={styles.candidateMetric}>Weighted visual heuristic score: {candidate.rankingScore.toFixed(2)} / 1.00</Text>
                    </Pressable>
                  ))}
                  {selectedCandidate ? (
                    <Text style={styles.muted}>Highlighted outline shows candidate {selectedCandidate.rank} in the captured image.</Text>
                  ) : null}
                </>
              )}
              <Text style={styles.sectionTitle}>Detected cues</Text>
              {result.visualCues.length ? result.visualCues.map((cue, index) => (
                <Text key={`${cue.className}-${index}`} style={styles.checklistItem}>• {cue.className} · model class confidence {Math.round(cue.modelConfidence * 100)}% (not a safety score)</Text>
              )) : <Text style={styles.muted}>No listed object cues were detected in this image.</Text>}
              {result.limitations.map((item) => <Text key={item} style={styles.muted}>{item}</Text>)}
              <Text style={styles.muted}>Model: {result.modelVersion}</Text>
              <Pressable accessibilityRole="button" onPress={() => void capture(true)} style={styles.secondaryButton}>
                <Text style={styles.secondaryText}>Retake photo</Text>
              </Pressable>
            </>
          )}
        </>
      )}
      {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
    </ScrollView>
  );
}
