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
  it('uses the Positron vector style and retains provider credits', () => {
    expect(BASEMAPS.streets.style).toBe('https://tiles.openfreemap.org/styles/positron');
    expect(BASEMAPS.streets.style).toContain('openfreemap.org');
    expect(BASEMAPS.satellite.style).toMatchObject({
      sources: { basemap: expect.objectContaining({ type: 'raster', attribution: expect.stringContaining('Esri') }) },
    });
    expect(BASEMAPS.satellite.style).toMatchObject({
      sources: { basemap: { attribution: 'Esri, Maxar, Earthstar Geographics' } },
    });
    expect(BASEMAPS.hybrid.style).toMatchObject({
      sources: {
        imagery: { type: 'raster', attribution: 'Esri, Maxar, Earthstar Geographics' },
        reference: { type: 'raster', attribution: 'Esri, Garmin, FAO, NOAA' },
      },
    });
    expect(BASEMAPS.terrain.style).toMatchObject({
      sources: { basemap: { type: 'raster', attribution: 'Esri, Maxar, Earthstar Geographics' } },
    });
  });
});
