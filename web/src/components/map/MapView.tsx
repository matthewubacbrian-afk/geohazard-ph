import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { HazardEvent } from '../../types/hazard';
import { BASEMAPS, type BasemapId } from './basemaps';
import styles from './MapView.module.css';

type MapViewProps = {
  events: HazardEvent[];
  basemap?: BasemapId;
  selectedEvent?: HazardEvent | null;
  showEvents?: boolean;
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

export default function MapView({
  events,
  basemap = 'streets',
  selectedEvent,
  showEvents = true,
}: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const appliedBasemap = useRef(basemap);

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

    map.setLayoutProperty('event-circles', 'visibility', showEvents ? 'visible' : 'none');

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

  // Keep the map and camera while replacing only its style.
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

    const restoreEvents = () => setupEventLayers(map);
    map.on('style.load', restoreEvents);
    appliedBasemap.current = basemap;

    return () => {
      map.off('style.load', restoreEvents);
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

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer('event-circles')) return;
    map.setLayoutProperty('event-circles', 'visibility', showEvents ? 'visible' : 'none');
  }, [showEvents]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || appliedBasemap.current === basemap) return;
    appliedBasemap.current = basemap;
    // Diff updates can remove custom layers without emitting style.load.
    // Full replacement guarantees our persistent listener restores markers.
    map.setStyle(BASEMAPS[basemap].style, { diff: false });
  }, [basemap]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !selectedEvent) return;
    const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
    map.flyTo({
      center: [selectedEvent.longitude, selectedEvent.latitude],
      zoom: Math.max(map.getZoom(), 8),
      duration: reducedMotion ? 0 : 800,
    });
    mapContainer.current?.scrollIntoView?.({
      block: 'nearest', behavior: reducedMotion ? 'auto' : 'smooth',
    });
  }, [selectedEvent]);

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
