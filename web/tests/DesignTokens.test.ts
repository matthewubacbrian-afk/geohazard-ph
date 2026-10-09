// @vitest-environment node
// @ts-expect-error Node built-in types are omitted from this web package's TypeScript config.
import { readFileSync } from 'node:fs';
// @ts-expect-error Node built-in types are omitted from this web package's TypeScript config.
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const tokenSheet = readFileSync(
  fileURLToPath(new URL('../src/styles/tokens.css', import.meta.url)),
  'utf8',
);
const requiredTokens = [
  '--surface',
  '--surface-raised',
  '--surface-container',
  '--risk-low',
  '--risk-moderate',
  '--risk-high',
  '--risk-very-high',
  '--magnitude-low',
  '--magnitude-moderate',
  '--magnitude-high',
  '--magnitude-very-high',
];
const riskTokens = requiredTokens.filter((token) => token.startsWith('--risk-'));
const magnitudeTokens = requiredTokens.filter((token) => token.startsWith('--magnitude-'));

function getHexValue(token: string): string {
  const declaration = tokenSheet.match(new RegExp(`${token}\\s*:\\s*(#[0-9a-fA-F]{6})`));
  expect(declaration, `${token} must have a direct six-digit hex value`).not.toBeNull();
  return declaration![1];
}

function channelToLinear(channel: number): number {
  const normalized = channel / 255;
  return normalized <= 0.04045 ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4;
}

function luminance(hex: string): number {
  const channels = hex.slice(1).match(/.{2}/g)!.map((value) => channelToLinear(parseInt(value, 16)));
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrastRatio(foreground: string, background: string): number {
  const values = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

describe('design tokens', () => {
  it('defines distinct risk and magnitude colors with accessible contrast on light surfaces', () => {
    for (const token of requiredTokens) {
      expect(tokenSheet, `missing required token ${token}`).toMatch(new RegExp(`${token}\\s*:`));
    }

    const riskColors = riskTokens.map(getHexValue);
    const magnitudeColors = magnitudeTokens.map(getHexValue);
    const surfaces = ['--surface', '--surface-raised', '--surface-container'].map(getHexValue);

    expect(new Set(riskColors)).not.toEqual(new Set(magnitudeColors));
    for (const foreground of [...riskColors, ...magnitudeColors]) {
      for (const background of surfaces) {
        expect(contrastRatio(foreground, background), `${foreground} on ${background}`).toBeGreaterThanOrEqual(4.5);
      }
    }
  });
});
