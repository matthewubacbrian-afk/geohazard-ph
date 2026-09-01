import { describe, expect, it } from 'vitest';

import { BASEMAPS, BASEMAP_IDS } from '../src/components/map/basemaps';

describe('BASEMAPS registry', () => {
  it('exposes exactly the four supported basemap ids in a stable order', () => {
    expect([...BASEMAP_IDS]).toEqual(['streets', 'satellite', 'hybrid', 'terrain']);
  });

  it('provides a label and a style spec for every basemap', () => {
    for (const id of BASEMAP_IDS) {
      const entry = BASEMAPS[id];
      expect(typeof entry.label).toBe('string');
      expect(entry.label.length).toBeGreaterThan(0);
      expect(entry.style).toBeTruthy();
    }
  });

  it('keys the registry by the same id each entry advertises', () => {
    for (const id of BASEMAP_IDS) {
      expect(BASEMAPS[id].id).toBe(id);
    }
  });

  it('ships streets as its first (default) entry', () => {
    expect(BASEMAP_IDS[0]).toBe('streets');
  });
});
