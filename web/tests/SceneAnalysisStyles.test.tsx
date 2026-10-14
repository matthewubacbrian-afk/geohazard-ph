// @vitest-environment node
// @ts-expect-error Node built-in types are omitted from this web package's TypeScript config.
import { readFileSync } from 'node:fs';
// @ts-expect-error Node built-in types are omitted from this web package's TypeScript config.
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const sceneAnalysisStyles = readFileSync(
  fileURLToPath(new URL('../src/pages/SceneAnalysis.module.css', import.meta.url)),
  'utf8',
);

describe('scene analysis candidate styling', () => {
  it('uses a neutral design token for polygon and selected-candidate highlights', () => {
    expect(sceneAnalysisStyles).toMatch(/\.candidateShape\s*\{[^}]*var\(--focus-ring\)/);
    expect(sceneAnalysisStyles).toMatch(/\.selected\s*\{[^}]*border-color:\s*var\(--focus-ring\)/);
    expect(sceneAnalysisStyles).not.toMatch(/\.(?:candidateShape|candidateShapeSelected|selected)\s*\{[^}]*var\(--(?:mineral|risk-low)\)/);
  });
});
