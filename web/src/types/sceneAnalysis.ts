export type SceneAnalysisRequest = {
  image_base64: string;
  mime_type: 'image/jpeg';
};

export type ImagePoint = { x: number; y: number };

export type CandidateRegion = {
  rank: number;
  surface_class: string;
  polygon: ImagePoint[];
  area_fraction: number;
  compactness: number;
  model_confidence: number;
  ranking_score: number;
};

export type VisualCue = { class_name: string; model_confidence: number };

export type SceneAnalysisResponse = {
  model_version: string;
  result_status: 'candidates_found' | 'no_clear_candidate';
  candidate_regions: CandidateRegion[];
  visual_cues: VisualCue[];
  limitations: string[];
};

export type SceneCapture = { previewUrl: string; imageBase64: string };
