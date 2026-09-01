import type { StyleSpecification } from 'maplibre-gl';

export type BasemapId = 'streets' | 'satellite' | 'hybrid' | 'terrain';

export type Basemap = {
  id: BasemapId;
  label: string;
  style: string | StyleSpecification;
};

export const BASEMAP_IDS: BasemapId[] = ['streets', 'satellite', 'hybrid', 'terrain'];

const ESRI_TILE_TEMPLATE = (service: string) =>
  `https://server.arcgisonline.com/ArcGIS/rest/services/${service}/MapServer/tile/{z}/{y}/{x}`;

// Raster-only style spec so the map stays light (no vector sprite/glyph deps)
// for the keyless ESRI World Imagery / Topo services.
function rasterStyle(tileUrl: string, label = 'basemap'): StyleSpecification {
  return {
    version: 8,
    sources: {
      basemap: {
        type: 'raster',
        tiles: [tileUrl],
        tileSize: 256,
        attribution: 'Esri, Maxar, Earthstar Geographics',
      },
    },
    layers: [
      {
        id: label,
        type: 'raster',
        source: 'basemap',
      },
    ],
  };
}

export const BASEMAPS: Record<BasemapId, Basemap> = {
  streets: {
    id: 'streets',
    label: 'Streets',
    style: 'https://tiles.openfreemap.org/styles/bright',
  },
  satellite: {
    id: 'satellite',
    label: 'Satellite',
    style: rasterStyle(ESRI_TILE_TEMPLATE('World_Imagery'), 'satellite'),
  },
  hybrid: {
    id: 'hybrid',
    label: 'Hybrid',
    // World Imagery with the reference (boundaries + places) labels overlaid.
    style: {
      version: 8,
      sources: {
        imagery: {
          type: 'raster',
          tiles: [ESRI_TILE_TEMPLATE('World_Imagery')],
          tileSize: 256,
          attribution: 'Esri, Maxar, Earthstar Geographics',
        },
        reference: {
          type: 'raster',
          tiles: [ESRI_TILE_TEMPLATE('Reference/World_Boundaries_and_Places')],
          tileSize: 256,
          attribution: 'Esri, Garmin, FAO, NOAA',
        },
      },
      layers: [
        { id: 'imagery', type: 'raster', source: 'imagery' },
        { id: 'reference-labels', type: 'raster', source: 'reference' },
      ],
    },
  },
  terrain: {
    id: 'terrain',
    label: 'Terrain',
    style: rasterStyle(ESRI_TILE_TEMPLATE('World_Topo_Map'), 'terrain'),
  },
};
