import { useId, useMemo } from 'react';
import type { FormEvent, Ref } from 'react';

import type { useMapLocations } from '../../hooks/useMapLocations';
import { findNearbyEarthquakes, LOCATION_RADII_KM } from '../../lib/savedLocations';
import type { HazardEvent } from '../../types/hazard';
import sidebarStyles from './DashboardSidebar.module.css';
import styles from './MapLocations.module.css';

type MapLocationsProps = {
  expanded: boolean;
  triggerRef: Ref<HTMLButtonElement>;
  onToggle: () => void;
  locations: ReturnType<typeof useMapLocations>;
  events: HazardEvent[];
  isLoading: boolean;
  hasError: boolean;
};

const RESULT_LIMIT = 10;

export default function MapLocations({
  expanded, triggerRef, onToggle, locations, events, isLoading, hasError,
}: MapLocationsProps) {
  const panelId = useId();
  const nearbyId = useId();
  const { point, radiusKm, mode, message, savedLocations } = locations;
  const nearby = useMemo(() =>
    expanded && point && !isLoading && !hasError ? findNearbyEarthquakes(events, point, radiusKm) : [],
  [events, expanded, hasError, isLoading, point, radiusKm]);

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = new FormData(event.currentTarget).get('locationName');
    if (typeof name === 'string' && locations.saveLocation(name)) event.currentTarget.reset();
  }

  return (
    <>
      <button ref={triggerRef} type="button" className={`${sidebarStyles.tab} ${styles.trigger}`} aria-expanded={expanded}
        aria-controls={panelId} onClick={onToggle}>
        My locations
      </button>
      <section id={panelId} className={styles.disclosure} aria-label="My locations" hidden={!expanded}>
        {expanded && <div className={styles.panel}>
          <div className={styles.actions}>
            <button type="button" disabled={mode === 'locating'} onClick={locations.useCurrentLocation}>
              {mode === 'locating' ? 'Finding location…' : 'Use my location'}
            </button>
            <button type="button" onClick={() => locations.changeMode(mode === 'picking' ? 'idle' : 'picking')}>
              {mode === 'picking' ? 'Cancel pin placement' : 'Drop a pin'}
            </button>
          </div>
          {mode === 'picking' && <p role="status">Select a point on the map to place your pin.</p>}
          {message && <p role="alert">{message}</p>}
          {point && <>
            <div className={styles.point}>
              <p>{point.latitude.toFixed(4)}°, {point.longitude.toFixed(4)}°</p>
              <button type="button" onClick={() => locations.selectPoint(null)}>Clear pin</button>
            </div>
            <label className={styles.field}>
              Radius
              <select value={radiusKm} onChange={(event) => locations.setRadiusKm(Number(event.target.value))}>
                {LOCATION_RADII_KM.map((radius) => <option key={radius} value={radius}>{radius} km</option>)}
              </select>
            </label>
            <form className={styles.field} onSubmit={save} key={`${point.latitude},${point.longitude}`}>
              <label className={styles.field}>
                Location name
                <input name="locationName" placeholder="e.g. Home" required maxLength={60} />
              </label>
              <button type="submit">Save location</button>
            </form>
          </>}
          <div className={styles.saved}>
            <h4>Saved locations</h4>
            <p>Saved in this browser.</p>
            {savedLocations.length === 0 ? <p>No saved locations yet.</p> : (
              <ul>
                {savedLocations.map((location) => (
                  <li key={location.name} className={styles.point}>
                    <button type="button" onClick={() => locations.openLocation(location)}>{location.name}</button>
                    <button type="button" aria-label={`Remove ${location.name}`}
                      onClick={() => locations.removeLocation(location.name)}>Remove</button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          {point && <section className={styles.nearby} aria-labelledby={nearbyId}>
            <h4 id={nearbyId}>Nearby earthquakes</h4>
            <p>Recorded events from the current dashboard filters, within {radiusKm} km of the pin.</p>
            {isLoading ? <p role="status">Loading earthquake records…</p>
              : hasError ? <p>Earthquake records are unavailable. Use Retry on the map.</p>
              : nearby.length === 0 ? <p>No matching earthquake records in this radius.</p>
              : <>
                <p role="status">
                  {nearby.length} matching {nearby.length === 1 ? 'record' : 'records'}.
                  {nearby.length > RESULT_LIMIT && ` Showing the latest ${RESULT_LIMIT}.`}
                </p>
                <ul>
                  {nearby.slice(0, RESULT_LIMIT).map(({ event, distance }) => (
                    <li key={event.id}>
                      <strong>{event.place_name || 'Recorded earthquake'}</strong>
                      <span>{distance.toFixed(1)} km · {event.magnitude == null ? 'Magnitude unavailable' : `M ${event.magnitude.toFixed(1)}`}</span>
                      <time dateTime={event.occurred_at}>{new Date(event.occurred_at).toLocaleString()}</time>
                    </li>
                  ))}
                </ul>
              </>}
          </section>}
        </div>}
      </section>
    </>
  );
}
