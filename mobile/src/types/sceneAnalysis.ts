export type ScenePoint = { x: number; y: number };

export type SceneCandidate = {
  rank: number;
  surfaceClass: string;
  polygon: ScenePoint[];
  areaFraction: number;
  compactness: number;
  modelConfidence: number;
  rankingScore: number;
};

export type SceneAnalysisResult = {
  modelVersion: string;
  resultStatus: 'candidates_found' | 'no_clear_candidate';
  candidateRegions: SceneCandidate[];
  visualCues: { className: string; modelConfidence: number }[];
  limitations: string[];
};

export type CapturedSceneImage = {
  uri: string;
  imageBase64: string;
  width: number;
  height: number;
};
