import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { HazardEvent } from '../../types/hazard';
import { BASEMAPS, type BasemapId } from './basemaps';
import styles from './MapView.module.css';

type MapViewProps = {
  events: HazardEvent[];
  basemap?: BasemapId;
};

const PH_CENTER: [number, number] = [121.774, 12.8797]; // Philippines

// Resolve a CSS custom property from :root (single source of truth for tokens).
// MapLibre paints need literal values, so we read the token at runtime instead
// of duplicating the color in source.
function cssVar(name: string, fallback = ''): string {
  if (typeof window === 'undefined') return fallback;
  return (
    window
      .getComputedStyle(document.documentElement)
      .getPropertyValue(name)
      .trim() || fallback
  );
}

function toFeatureCollection(events: HazardEvent[]) {
  return {
    type: 'FeatureCollection' as const,
    features: events.map((event) => ({
      type: 'Feature' as const,
      geometry: {
        type: 'Point' as const,
        coordinates: [event.longitude, event.latitude],
      },
      properties: {
        place: event.place_name,
        magnitude: event.magnitude ?? null,
      },
    })),
  };
}

export default function MapView({ events, basemap = 'streets' }: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const skipNextBasemapSwitch = useRef(true);

  // Always-current events, readable from inside event handlers that were
  // registered once at mount (those closures would otherwise see whatever
  // `events` was on the render that registered them, not later updates).
  const eventsRef = useRef(events);
  eventsRef.current = events;

  // Setup the events source and event-circles layer.
  // Must run after initial map load AND after every style change
  // because setStyle() wipes custom sources/layers. Reads from eventsRef so
  // it always uses the latest data, even though it's registered once.
  const setupEventLayers = (map: maplibregl.Map) => {
    // Check if source already exists and remove it to avoid duplication
    if (map.getSource('events')) {
      if (map.getLayer('event-circles')) {
        map.removeLayer('event-circles');
      }
      map.removeSource('events');
    }

    map.addSource('events', {
      type: 'geojson',
      data: toFeatureCollection(eventsRef.current),
    });

    const markerColor = cssVar('--accent');
    const markerStroke = cssVar('--white') || 'var(--white)';

    map.addLayer({
      id: 'event-circles',
      type: 'circle',
      source: 'events',
      paint: {
        'circle-radius': [
          'interpolate',
          ['linear'],
          ['coalesce', ['get', 'magnitude'], 0],
          0,
          8,
          9,
          22,
        ],
        'circle-color': markerColor,
        'circle-stroke-width': 1.5,
        'circle-stroke-color': markerStroke,
        'circle-opacity': 0.9,
      },
    });

    if (map.getLayer('label_country')) {
      map.setLayoutProperty('label_country', 'text-field', [
        'format',
        ['get', 'name_en'],
        { 'font-scale': 1.2 },
        '\n',
        {},
        ['get', 'name'],
        {
          'font-scale': 0.8,
          'text-font': ['literal', ['Noto Sans Regular']],
        },
      ]);
    }
  };

  // Create the map exactly ONCE, on mount. Basemap changes are applied via
  // setStyle in the effect below rather than recreating the map (cheaper,
  // and preserves the camera); event-data changes are pushed into the
  // existing source via setData in the effect below that too — NOT by
  // recreating the map. Recreating the map on every `events` change was the
  // actual bug: `events` commonly arrives as a new array reference on
  // re-renders that have nothing to do with its contents (e.g. switching
  // basemap re-renders the parent), and destroying+recreating the map on
  // every one of those resets the camera to PH_CENTER/zoom 5 regardless of
  // any style.load camera-restore logic, because the whole map instance —
  // camera included — is thrown away.
  useEffect(() => {
    if (!mapContainer.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: BASEMAPS[basemap].style,
      center: PH_CENTER,
      zoom: 5,
    });
    mapRef.current = map;

    map.addControl(new maplibregl.NavigationControl(), 'top-right');

    // Setup event layers on initial map load
    map.on('load', () => {
      setupEventLayers(map);
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // Mount-only intentionally: see comment above. `basemap`'s initial value
    // is captured here; later changes are handled by the basemap effect.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Sync updated event data into the already-existing source. This runs on
  // every `events` change WITHOUT touching the map instance or camera.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const source = map.getSource('events') as maplibregl.GeoJSONSource | undefined;
    // If the source isn't there yet (map/style still loading), the 'load' /
    // 'style.load' handlers will pick up eventsRef.current when they run.
    if (!source) return;
    source.setData(toFeatureCollection(events));
  }, [events]);

  // Swap the basemap in place. The first render is skipped because the Map
  // constructor already applied the starting style.
  //
  // CRITICAL: Listen for 'style.load' (not 'load'!) because:
  // - 'load' fires only ONCE when the map is first created
  // - 'style.load' fires every time a new style is loaded via setStyle()
  //
  // Restore camera state and re-add event layers that were wiped by setStyle.
  useEffect(() => {
    if (skipNextBasemapSwitch.current) {
      skipNextBasemapSwitch.current = false;
      return;
    }
    const map = mapRef.current;
    if (!map) return;

    const camera = {
      center: map.getCenter().toArray() as [number, number],
      zoom: map.getZoom(),
      bearing: map.getBearing(),
      pitch: map.getPitch(),
    };

    // When the new style is fully loaded, restore camera and re-add event layers
    map.once('style.load', () => {
      // Restore camera state instantly (duration: 0)
      map.flyTo({
        center: camera.center,
        zoom: camera.zoom,
        bearing: camera.bearing,
        pitch: camera.pitch,
        duration: 0,
      });

      // Re-add event layers (wiped by setStyle)
      setupEventLayers(map);
    });

    map.setStyle(BASEMAPS[basemap].style);
  }, [basemap]);

  return (
    <div className={styles.canvas} aria-label="Hazard map">
      <div ref={mapContainer} className={styles.container} />
      <span className="sr-only">{events.length} events loaded</span>
      {events.length === 0 && (
        <div className={styles.empty}>No events to display.</div>
      )}
    </div>
  );
}
