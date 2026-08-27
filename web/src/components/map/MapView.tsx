import type { HazardEvent } from '../../types/hazard';

type MapViewProps = {
  events: HazardEvent[];
};

export default function MapView({ events }: MapViewProps) {
  return (
    <section className="map-shell" aria-label="Hazard map">
      <div className="map-placeholder">
        <span>MapLibre map area</span>
        <strong>{events.length}</strong>
        <span>events loaded</span>
      </div>
    </section>
  );
}
