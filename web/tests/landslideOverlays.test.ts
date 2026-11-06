import { describe, expect, it, vi } from 'vitest';

import {
  LANDSLIDE_ATTRIBUTION,
  LANDSLIDE_IMAGE_SERVICE,
  LANDSLIDE_LAYER_ID,
  removeLandslideOverlay,
  syncLandslideOverlay,
} from '../src/components/map/landslideOverlays';

function createMap() {
  const sources = new Set<string>();
  const layers = new Set<string>();
  return {
    addSource: vi.fn((id: string) => sources.add(id)),
    addLayer: vi.fn((layer: { id: string }) => layers.add(layer.id)),
    getSource: vi.fn((id: string) => sources.has(id) ? { id } : undefined),
    getLayer: vi.fn((id: string) => layers.has(id) ? { id } : undefined),
    setLayoutProperty: vi.fn(),
    removeLayer: vi.fn((id: string) => layers.delete(id)),
    removeSource: vi.fn((id: string) => sources.delete(id)),
  };
}

describe('landslide susceptibility map overlay', () => {
  it('adds the remote NASA export tiles with source attribution', () => {
    const map = createMap();

    syncLandslideOverlay(map as never, true);

    expect(map.addSource).toHaveBeenCalledWith(LANDSLIDE_LAYER_ID, expect.objectContaining({
      type: 'raster',
      tiles: [expect.stringContaining(`${LANDSLIDE_IMAGE_SERVICE}/exportImage?bbox={bbox-epsg-3857}`)],
      attribution: LANDSLIDE_ATTRIBUTION,
    }));
    expect(map.addLayer.mock.calls[0]?.[0]).toEqual(expect.objectContaining({
      id: LANDSLIDE_LAYER_ID,
      type: 'raster',
      paint: expect.objectContaining({ 'raster-opacity': expect.any(Number) }),
    }));
  });

  it('hides an existing NASA layer when disabled and removes it on cleanup', () => {
    const map = createMap();
    syncLandslideOverlay(map as never, true);

    syncLandslideOverlay(map as never, false);
    expect(map.setLayoutProperty).toHaveBeenCalledWith(LANDSLIDE_LAYER_ID, 'visibility', 'none');

    removeLandslideOverlay(map as never);
    expect(map.removeLayer).toHaveBeenCalledWith(LANDSLIDE_LAYER_ID);
    expect(map.removeSource).toHaveBeenCalledWith(LANDSLIDE_LAYER_ID);
  });
});
