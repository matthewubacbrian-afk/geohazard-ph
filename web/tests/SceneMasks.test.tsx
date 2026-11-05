import { describe, expect, it } from 'vitest';
import { sceneFromMasks } from '../src/services/sceneMasks';

const mask = (label: string, rows: number[][], score = 0.9) => ({
  label, score, mask: { width: rows[0].length, height: rows.length,
    data: Uint8Array.from(rows.flat().map((value) => value * 255)) },
});

describe('local scene mask evidence', () => {
  it('finds separated floor components and returns closed bounded contours with real model scores', () => {
    const result = sceneFromMasks([mask('floor-tile', [
      [1, 1, 0, 1], [1, 1, 0, 1], [0, 0, 0, 1], [0, 0, 0, 0],
    ])]);
    expect(result.candidate_regions).toHaveLength(2);
    for (const candidate of result.candidate_regions) {
      expect(candidate.model_confidence).toBe(0.9);
      expect(candidate.polygon[0]).toEqual(candidate.polygon[candidate.polygon.length - 1]);
      expect(candidate.polygon.length).toBeGreaterThanOrEqual(5);
      expect(candidate.polygon.length).toBeLessThanOrEqual(64);
      expect(candidate.polygon.every(({ x, y }) => x >= 0 && x <= 1 && y >= 0 && y <= 1)).toBe(true);
    }
    expect(result.candidate_regions[0].area_fraction).toBe(4 / 16);
  });
  it('retains object cues without inventing ground candidates or valid scores', () => {
    const result = sceneFromMasks([mask('person', [[1, 1], [1, 1]]), mask('road', [[1]], NaN)]);
    expect(result.result_status).toBe('no_clear_candidate');
    expect(result.visual_cues).toEqual([{ class_name: 'person', model_confidence: 0.9 }]);
  });
  it('traces a concave mask instead of an enclosing rectangle', () => {
    const result = sceneFromMasks([mask('grass', [[1, 0, 0], [1, 0, 0], [1, 1, 1]])]);
    expect(result.candidate_regions[0].polygon.length).toBeGreaterThan(5);
    expect(result.candidate_regions[0].area_fraction).toBeCloseTo(5 / 9);
  });
  it('resolves the model placeholder for the official merged-grass category', () => {
    const result = sceneFromMasks([mask('LABEL_193', [[1, 1], [1, 1]])]);
    expect(result.visual_cues[0].class_name).toBe('grass-merged');
    expect(result.candidate_regions[0].surface_class).toBe('grass');
  });
  it('rejects inconsistent mask dimensions', () => {
    expect(() => sceneFromMasks([{label: 'road', score: 0.9, mask: {width: 3, height: 3, data: new Uint8Array(2)}}])).toThrow();
  });
});
