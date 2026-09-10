import type { Map } from 'maplibre-gl';

export type VolcanoOverlayState = 'loading' | 'ready' | 'error';
export const VOLCANO_MAP_BASE = 'https://gisweb.phivolcs.dost.gov.ph/arcgis/rest/services/PHIVOLCSPublic';
export const VOLCANO_OVERLAYS = [
  { id: 'phivolcs-lahar', service: 'VolcanoLahar', label: 'Lahar' },
  { id: 'phivolcs-lava', service: 'Lava', label: 'Lava flows' },
  { id: 'phivolcs-pyroclastic', service: 'Pyroclastic', label: 'Pyroclastic density currents' },
  { id: 'phivolcs-base-surge', service: 'BaseSurge', label: 'Base surge' },
] as const;

export function isVolcanoOverlay(id?: string): boolean {
  return VOLCANO_OVERLAYS.some(layer => layer.id === id);
}

export function syncVolcanoOverlays(map: Map, enabled: boolean): void {
  for (const layer of VOLCANO_OVERLAYS) {
    if (enabled && !map.getSource(layer.id)) {
      map.addSource(layer.id, {
        type: 'raster',
        tiles: [`${VOLCANO_MAP_BASE}/${layer.service}/MapServer/export?bbox={bbox-epsg-3857}` +
          '&bboxSR=3857&imageSR=3857&size=256,256&format=png32&transparent=true&layers=show:0&f=image'],
        tileSize: 256,
        bounds: [119.9, 5.9, 126.2, 20.5],
        attribution: '<a href="https://gisweb.phivolcs.dost.gov.ph/gisweb/">DOST-PHIVOLCS volcano hazard maps</a>',
      });
    }
    if (enabled && !map.getLayer(layer.id)) {
      map.addLayer({
        id: layer.id, type: 'raster', source: layer.id,
        paint: { 'raster-opacity': 0.65, 'raster-fade-duration': 0 },
      }, map.getLayer('volcano-zones') ? 'volcano-zones' : undefined);
    }
    if (map.getLayer(layer.id)) {
      map.setLayoutProperty(layer.id, 'visibility', enabled ? 'visible' : 'none');
    }
  }
}

export function removeVolcanoOverlays(map: Map): void {
  for (const { id } of VOLCANO_OVERLAYS) {
    if (map.getLayer(id)) map.removeLayer(id);
    if (map.getSource(id)) map.removeSource(id);
  }
}
