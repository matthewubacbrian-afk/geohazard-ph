import type { Map } from 'maplibre-gl';

export type LandslideOverlayState = 'loading' | 'ready' | 'error';

export const LANDSLIDE_IMAGE_SERVICE =
  'https://gis.earthdata.nasa.gov/portal/rest/services/Landslides/Global_Landslide_Susceptibility/ImageServer';
export const LANDSLIDE_OVERLAY_SOURCE_URL =
  'https://gis.earthdata.nasa.gov/portal/home/item.html?id=d9c8e1279e3e48c2ab3dd318a6649b3a';
export const LANDSLIDE_LAYER_ID = 'nasa-landslide-susceptibility';
export const LANDSLIDE_ATTRIBUTION =
  `<a href="${LANDSLIDE_OVERLAY_SOURCE_URL}" target="_blank" rel="noreferrer">NASA Global Landslide Susceptibility Map</a>`;

function rasterSource() {
  return {
    type: 'raster' as const,
    tiles: [`${LANDSLIDE_IMAGE_SERVICE}/exportImage?bbox={bbox-epsg-3857}` +
      '&bboxSR=3857&imageSR=3857&size=256,256&format=png32&transparent=true&f=image'],
    tileSize: 256,
    attribution: LANDSLIDE_ATTRIBUTION,
  };
}

export function isLandslideOverlay(id?: string): boolean {
  return id === LANDSLIDE_LAYER_ID;
}

export function syncLandslideOverlay(map: Map, enabled: boolean): void {
  if (enabled && !map.getSource(LANDSLIDE_LAYER_ID)) {
    map.addSource(LANDSLIDE_LAYER_ID, rasterSource());
  }
  if (enabled && !map.getLayer(LANDSLIDE_LAYER_ID)) {
    map.addLayer({
      id: LANDSLIDE_LAYER_ID,
      type: 'raster',
      source: LANDSLIDE_LAYER_ID,
      paint: { 'raster-opacity': 0.68, 'raster-fade-duration': 0 },
    }, map.getLayer('event-circles') ? 'event-circles' : undefined);
  }
  if (map.getLayer(LANDSLIDE_LAYER_ID)) {
    map.setLayoutProperty(LANDSLIDE_LAYER_ID, 'visibility', enabled ? 'visible' : 'none');
  }
}

export function removeLandslideOverlay(map: Map): void {
  if (map.getLayer(LANDSLIDE_LAYER_ID)) map.removeLayer(LANDSLIDE_LAYER_ID);
  if (map.getSource(LANDSLIDE_LAYER_ID)) map.removeSource(LANDSLIDE_LAYER_ID);
}
