import type { CandidateRegion, ImagePoint, SceneAnalysisResponse } from '../types/sceneAnalysis';

export const SCENE_MODEL = 'Xenova/detr-resnet-50-panoptic';
export const SCENE_REVISION = 'ea24b2d4e0bfae31f0a1299ba3fb892a2df064de';
export const SCENE_LIMITATIONS = [
  'Visual scene cues only; this result does not determine whether any area is safe.',
  'Blur, obstruction, lighting, or viewpoint can hide visual cues. A single image cannot verify structural integrity, earthquake resistance, ground conditions, falling-glass or electrical hazards, egress, accessibility, routes, unseen areas, or changing conditions.',
];
const SURFACES = new Set(['floor-other', 'floor-stone', 'floor-tile', 'floor-wood', 'ground-other', 'road', 'pavement', 'grass', 'gravel']);
// Missing names in the converted model config, from COCO's official panoptic taxonomy:
// https://github.com/cocodataset/panopticapi/blob/cf0760099461dfd87e284e768bc43cfbf733c871/panoptic_coco_categories.json
const MERGED_LABELS: Record<string, string> = {
  LABEL_184: 'tree-merged', LABEL_185: 'fence-merged', LABEL_186: 'ceiling-merged',
  LABEL_187: 'sky-other-merged', LABEL_188: 'cabinet-merged', LABEL_189: 'table-merged',
  LABEL_190: 'floor-other-merged', LABEL_191: 'pavement-merged', LABEL_192: 'mountain-merged',
  LABEL_193: 'grass-merged', LABEL_194: 'dirt-merged', LABEL_195: 'paper-merged',
  LABEL_196: 'food-other-merged', LABEL_197: 'building-other-merged', LABEL_198: 'rock-merged',
  LABEL_199: 'wall-other-merged', LABEL_200: 'rug-merged',
};
const SURFACE_ALIASES: Record<string, string> = {
  'floor-other-merged': 'floor-other', 'pavement-merged': 'pavement', 'grass-merged': 'grass',
};
export type SceneMask = {
  label: string; score: number;
  mask: { width: number; height: number; data: Uint8Array | Uint8ClampedArray };
};
type Point = [number, number];

function simplify(points: Point[], tolerance: number): Point[] {
  const kept = new Set([0, points.length - 1]);
  const pending: Point[] = [[0, points.length - 1]];
  while (pending.length) {
    const [first, last] = pending.pop()!;
    const [ax, ay] = points[first], [bx, by] = points[last];
    const length = Math.hypot(bx - ax, by - ay);
    let farthest = -1, distance = -1;
    for (let i = first + 1; i < last; i++) {
      const [x, y] = points[i];
      const d = length ? Math.abs((by - ay) * x - (bx - ax) * y + bx * ay - by * ax) / length
        : Math.hypot(x - ax, y - ay);
      if (d > distance) { distance = d; farthest = i; }
    }
    if (distance > tolerance) {
      kept.add(farthest); pending.push([first, farthest], [farthest, last]);
    }
  }
  return [...kept].sort((a, b) => a - b).map((index) => points[index]);
}

function contour(labels: Int32Array, label: number, startIndex: number, width: number,
  height: number, perimeter: number): ImagePoint[] {
  const matches = (x: number, y: number) => x >= 0 && y >= 0 && x < width && y < height
    && labels[y * width + x] === label;
  const start: Point = [startIndex % width, Math.floor(startIndex / width)];
  let current = start, previous: Point | null = null;
  const boundary: Point[] = [];
  const stride = Math.max(1, Math.ceil(perimeter / 2048));
  for (let step = 0; step <= perimeter; step++) {
    if (step % stride === 0) boundary.push(current);
    const [x, y] = current;
    const options: Point[] = [];
    if (matches(x, y) && !matches(x, y - 1)) options.push([x + 1, y]);
    if (matches(x - 1, y) && !matches(x, y)) options.push([x, y + 1]);
    if (matches(x - 1, y - 1) && !matches(x - 1, y)) options.push([x - 1, y]);
    if (matches(x, y - 1) && !matches(x - 1, y - 1)) options.push([x, y - 1]);
    if (!options.length) break;
    if (previous) {
      const ix = x - previous[0], iy = y - previous[1];
      const priority = ([nx, ny]: Point) => {
        const ox = nx - x, oy = ny - y, cross = ix * oy - iy * ox;
        return cross > 0 ? 0 : cross === 0 && ix === ox && iy === oy ? 1 : cross < 0 ? 2 : 3;
      };
      options.sort((a, b) => priority(a) - priority(b));
    }
    previous = current; current = options[0];
    if (current[0] === start[0] && current[1] === start[1]) break;
  }
  boundary.push(start);
  let tolerance = 0.25;
  let polygon = simplify(boundary, tolerance);
  while (polygon.length > 64) { tolerance *= 1.5; polygon = simplify(boundary, tolerance); }
  // Keep four distinct vertices even for a single-pixel component.
  if (polygon.length < 5) polygon = simplify(boundary, 0);
  if (polygon.length < 5 || polygon.length > 64) return [];
  return polygon.map(([x, y]) => ({ x: x / width, y: y / height }));
}

export function sceneFromMasks(segments: SceneMask[]): SceneAnalysisResponse {
  const cues = new Map<string, number>();
  const components: Array<Omit<CandidateRegion, 'rank' | 'ranking_score'> & { area: number; start: number }> = [];
  for (const { label: rawLabel, score, mask } of segments) {
    const label = MERGED_LABELS[rawLabel] ?? rawLabel;
    if (!label || !Number.isFinite(score) || score < 0 || score > 1) continue;
    if (label.startsWith('LABEL_')) continue;
    cues.set(label, Math.max(cues.get(label) ?? 0, score));
    const surface = SURFACE_ALIASES[label] ?? label;
    if (!SURFACES.has(surface) || score < 0.5) continue;
    const { width, height, data } = mask;
    if (!Number.isInteger(width) || !Number.isInteger(height) || width <= 0 || height <= 0
      || width > 512 || height > 512 || data.length !== width * height) throw new Error('Invalid segmentation mask');
    const labels = new Int32Array(data.length), queue = new Int32Array(data.length);
    let labelId = 0;
    for (let start = 0; start < data.length; start++) {
      if (!data[start] || labels[start]) continue;
      labelId++; let head = 0, tail = 1, perimeter = 0;
      queue[0] = start; labels[start] = labelId;
      while (head < tail) {
        const index = queue[head++], x = index % width, y = Math.floor(index / width);
        for (const next of [x > 0 ? index - 1 : -1, x + 1 < width ? index + 1 : -1,
          y > 0 ? index - width : -1, y + 1 < height ? index + width : -1]) {
          if (next < 0 || !data[next]) { perimeter++; continue; }
          if (!labels[next]) { labels[next] = labelId; queue[tail++] = next; }
        }
      }
      if (tail < Math.ceil(data.length * 0.01)) continue;
      const polygon = contour(labels, labelId, start, width, height, perimeter);
      if (!polygon.length) continue;
      components.push({ surface_class: surface, polygon, area: tail, start,
        area_fraction: tail / data.length, compactness: Math.min(1, 4 * Math.PI * tail / perimeter ** 2),
        model_confidence: score });
    }
  }
  const largest = Math.max(1, ...components.map(({ area }) => area));
  const ranked = components.map((component) => ({ ...component,
    ranking_score: component.area / largest * 0.5 + component.compactness * 0.3 + component.model_confidence * 0.2,
  })).sort((a, b) => b.ranking_score - a.ranking_score || b.area - a.area || a.start - b.start
    || a.surface_class.localeCompare(b.surface_class));
  const candidates = ranked.slice(0, 5).map(({ area: _area, start: _start, ...candidate }, index) => ({
    ...candidate, rank: index + 1,
  }));
  return {
    model_version: `${SCENE_MODEL}@${SCENE_REVISION}:q8:browser-512:coco-cf076009`,
    result_status: candidates.length ? 'candidates_found' : 'no_clear_candidate',
    candidate_regions: candidates,
    visual_cues: [...cues].sort(([a], [b]) => a.localeCompare(b))
      .map(([class_name, model_confidence]) => ({ class_name, model_confidence })),
    limitations: [...SCENE_LIMITATIONS],
  };
}
