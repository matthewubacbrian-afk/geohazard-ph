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

export default function MapView({ events, basemap = 'streets' }: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const skipNextBasemapSwitch = useRef(true);

  // Create the map once with the initial basemap. A style switch is applied via
  // setStyle below rather than recreating the map, so basemap changes stay
  // cheap and the viewport/zoom are preserved.
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

    // Runs on the initial load AND after every setStyle, because a style
    // swap wipes custom sources/layers and emits a fresh 'load' event.
    map.on('load', () => {
      map.addSource('events', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
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
        },
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
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // `events` intentionally drives the map layer data. Recreation on `events`
    // change reuses the current `basemap` closure, so the drawn style stays in
    // sync even though `basemap` is not listed here.
  }, [events]);

  // Swap the basemap in place. The first render is skipped because the Map
  // constructor already applied the starting style.
  useEffect(() => {
    if (skipNextBasemapSwitch.current) {
      skipNextBasemapSwitch.current = false;
      return;
    }
    mapRef.current?.setStyle(BASEMAPS[basemap].style);
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
