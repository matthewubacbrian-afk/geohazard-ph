import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { HazardEvent } from '../../types/hazard';

type MapViewProps = {
  events: HazardEvent[];
};

export default function MapView({ events }: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mapContainer.current) return;

    

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://tiles.openfreemap.org/styles/bright',
      center: [121.774, 12.8797], // Philippines
      zoom: 5,
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');

    map.on('load', () => {
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
    });

    return () => map.remove();
  }, []);

  return (
    <section className="map-shell" aria-label="Hazard map">
      <div ref={mapContainer} className="map-container" />
      <span className="sr-only">{events.length} events loaded</span>
    </section>
  );
}