import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { describe, expect, it } from 'vitest';

import {
  buildProvenance,
  countFeatureVertices,
  DEFAULT_SOURCE_URL,
  DEFAULT_TOLERANCE,
  QUANTIZATION_DECIMALS,
  serializeGeoJson,
  simplifyGeoJson
} from './generate-regions.mjs';

const source = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { shapeName: 'Test Region', ignored: 'removed' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [0, 0],
          [1, 0.01],
          [2, 0],
          [2, 2],
          [0, 2],
          [0, 0]
        ]]
      }
    },
    {
      type: 'Feature',
      properties: { shapeName: 'Island Region' },
      geometry: {
        type: 'MultiPolygon',
        coordinates: [[[
          [3, 0],
          [4, 0],
          [4, 1],
          [3, 1],
          [3, 0]
        ]]]
      }
    }
  ]
};

source.features.push(...Array.from({ length: 15 }, (_, index) => ({
  type: 'Feature',
  properties: { shapeName: `Synthetic Region ${index + 1}` },
  geometry: {
    type: 'Polygon',
    coordinates: [[
      [10 + index, 0],
      [11 + index, 0],
      [11 + index, 1],
      [10 + index, 1],
      [10 + index, 0]
    ]]
  }
})));

describe('generate-regions helpers', () => {
  it('uses a real pinned source and geometry-preserving defaults', () => {
    expect(DEFAULT_SOURCE_URL).toBe(
      'https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/41af8f1/releaseData/gbOpen/PHL/ADM1/geoBoundaries-PHL-ADM1.geojson'
    );
    expect(DEFAULT_TOLERANCE).toBeGreaterThanOrEqual(0.005);
    expect(DEFAULT_TOLERANCE).toBeLessThanOrEqual(0.01);
    expect(QUANTIZATION_DECIMALS).toBe(3);
  });

  it('keeps the checked-in asset within size and small-region detail bounds', () => {
    const assetPath = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../src/data/philippine-regions.json');
    const asset = JSON.parse(fs.readFileSync(assetPath, 'utf8'));
    const ncr = asset.features.find((feature) => feature.properties.region_name === 'NCR');

    expect(Buffer.byteLength(fs.readFileSync(assetPath))).toBeLessThan(500 * 1024);
    expect(countFeatureVertices(ncr)).toBeGreaterThanOrEqual(20);
  });

  it('simplifies polygon and multipolygon rings while preserving closure and names', () => {
    const result = simplifyGeoJson(source, 0.1);

    expect(result.features.slice(0, 2).map(({ properties, geometry }) => ({ properties, type: geometry.type }))).toEqual([
      { properties: { region_name: 'Test Region' }, type: 'Polygon' },
      { properties: { region_name: 'Island Region' }, type: 'MultiPolygon' }
    ]);
    expect(result.features[0].geometry.coordinates[0][0]).toEqual(
      result.features[0].geometry.coordinates[0].at(-1)
    );
    expect(result.features[0].geometry.coordinates[0].length).toBeLessThan(
      source.features[0].geometry.coordinates[0].length
    );
  });

  it('counts coordinate pairs in nested geometry coordinates', () => {
    const result = simplifyGeoJson(source, 0.1);

    expect(countFeatureVertices(result.features[0])).toBe(5);
    expect(countFeatureVertices(result.features[1])).toBe(5);
  });

  it('serializes identical source and tolerance to identical bytes', () => {
    const first = serializeGeoJson(simplifyGeoJson(source, 0.1));
    const second = serializeGeoJson(simplifyGeoJson(source, 0.1));

    expect(Buffer.byteLength(first)).toBe(Buffer.byteLength(second));
    expect(first).toBe(second);
  });

  it('builds provenance with attribution and per-region vertex counts', () => {
    const features = simplifyGeoJson(source, 0.1).features;
    const provenance = buildProvenance({
      sourceMetadata: {
        boundaryID: 'PHL-ADM1-36201628',
        boundaryYearRepresented: '2020',
        buildDate: 'Jul 05, 2023',
        boundarySource: 'NAMRIA, PSA, OCHA Philippines',
        boundaryLicense: 'CC BY 3.0 IGO'
      },
      sourceUrl: 'https://example.test/regions.geojson',
      tolerance: 0.1,
      outputBytes: 1234,
      features,
      generatedAt: '2026-09-12T00:00:00.000Z'
    });

    expect(provenance).toContain(
      'Philippine administrative boundaries © geoBoundaries, sourced from NAMRIA, PSA, and OCHA Philippines, licensed under CC BY 3.0 IGO.'
    );
    expect(provenance).toContain('| Test Region | 5 |');
    expect(provenance).toContain('| Island Region | 5 |');
    expect(provenance).toContain('Output bytes: 1,234');
  });

  it('rejects invalid tolerances and malformed sources', () => {
    expect(() => simplifyGeoJson(source, 0)).toThrow(/tolerance/i);
    expect(() => simplifyGeoJson({ type: 'FeatureCollection', features: [] }, 0.1)).toThrow(/feature/i);
    expect(() => simplifyGeoJson({
      type: 'FeatureCollection',
      features: Array.from({ length: 17 }, () => ({ properties: {}, geometry: null }))
    }, 0.1)).toThrow(/shapeName/i);
  });
});