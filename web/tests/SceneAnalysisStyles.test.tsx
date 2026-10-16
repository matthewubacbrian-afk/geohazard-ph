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

  it('uses a roomy desktop capture workspace with a stacked narrow layout', () => {
    expect(sceneAnalysisStyles).toMatch(/\.workspace\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1\.75fr\)/);
    expect(sceneAnalysisStyles).toMatch(/@media\s*\(max-width:\s*700px\)[\s\S]*?\.workspace\s*\{[^}]*grid-template-columns:\s*1fr/);
    expect(sceneAnalysisStyles).toMatch(/\.viewfinder\s*\{[^}]*aspect-ratio:\s*4\s*\/\s*3/);
  });

  it('styles the new camera controls and visible keyboard focus', () => {
    expect(sceneAnalysisStyles).toMatch(/\.primaryButton\s*\{/);
    expect(sceneAnalysisStyles).toMatch(/\.toggleRow\s*\{/);
    expect(sceneAnalysisStyles).toMatch(/\.zoomControl input\[type="range"\]/);
    expect(sceneAnalysisStyles).toMatch(/:focus-visible[^}]*outline:\s*3px solid var\(--focus-ring\)/);
  });
});
