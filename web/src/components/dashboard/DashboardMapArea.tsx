import type { StaticLayer } from '../../types/staticLayer';
import type { VolcanoOverlayState } from '../map/volcanoOverlays';
import type { LandslideOverlayState } from '../map/landslideOverlays';
import styles from "./DashboardMapArea.module.css";
import Skeleton from "../common/Skeleton";
import DashboardSummaryBar from './DashboardSummaryBar';
import MapView from "../map/MapView";
import type { BasemapId } from "../map/basemaps";
import type { HazardEvent } from "../../types/hazard";
import { useRiskProfiles } from "../../hooks/useRiskProfiles";

type DashboardMapAreaProps = {
  events: HazardEvent[];
  faults?: StaticLayer[];
  volcanoZones?: StaticLayer[];
  showFaults?: boolean;
  showVolcanoZones?: boolean;
  volcanoOverlayRevision?: number;
  onVolcanoOverlayState?: (state: VolcanoOverlayState) => void;
  showLandslideSusceptibility?: boolean;
  landslideOverlayRevision?: number;
  onLandslideOverlayState?: (state: LandslideOverlayState) => void;
  isLoading: boolean;
  error: Error | null;
  onRetry: () => void;
  basemap?: BasemapId;
  selectedEvent?: HazardEvent | null;
  onSelectEvent?: (event: HazardEvent) => void;
  showEvents?: boolean;
  showRiskLayer?: boolean;
};

const RISK_LABELS = [
  { label: 'Very High', swatch: 'swatch--very-high' },
  { label: 'High', swatch: 'swatch--high' },
  { label: 'Moderate', swatch: 'swatch--medium' },
  { label: 'Low', swatch: 'swatch--low' },
] as const;

export default function DashboardMapArea({
  events,
  faults, volcanoZones, showFaults, showVolcanoZones,
  volcanoOverlayRevision, onVolcanoOverlayState,
  showLandslideSusceptibility = false,
  landslideOverlayRevision,
  onLandslideOverlayState,
  isLoading,
  error,
  onRetry,
  basemap = "streets",
  selectedEvent,
  onSelectEvent,
  showEvents = true,
  showRiskLayer = true,
}: DashboardMapAreaProps) {
  const {
    data: riskProfiles = [],
    error: riskProfilesError,
    refetch: refetchRiskProfiles,
  } = useRiskProfiles();

  return (
    <main className={styles.mapArea} aria-label="Geospatial risk dashboard map">
      <MapView
        events={events}
        faults={faults} volcanoZones={volcanoZones}
        showFaults={showFaults} showVolcanoZones={showVolcanoZones}
        volcanoOverlayRevision={volcanoOverlayRevision}
        onVolcanoOverlayState={onVolcanoOverlayState}
        showLandslideSusceptibility={showLandslideSusceptibility}
        landslideOverlayRevision={landslideOverlayRevision}
        onLandslideOverlayState={onLandslideOverlayState}
        basemap={basemap}
        selectedEvent={selectedEvent}
        onSelectEvent={onSelectEvent}
        showEvents={showEvents}
        riskProfiles={riskProfiles}
        showRiskLayer={showRiskLayer}
      />

      <DashboardSummaryBar events={events} isLoading={isLoading} error={error} />

      {isLoading && !error && (
        <div className={styles.status} role="status">
          <Skeleton width={120} height={16} />
          <span className={styles.statusText}>Loading events…</span>
        </div>
      )}

      {error && (
        <div className={`${styles.status} ${styles["status--error"]}`} role="alert">
          <p className={styles.statusText}>Failed to load events.</p>
          <button type="button" className={styles.retryBtn} onClick={onRetry}>
            Retry
          </button>
        </div>
      )}

      {showRiskLayer && riskProfilesError && (
        <div className={`${styles.status} ${styles["status--error"]}`} role="alert">
          <p className={styles.statusText}>Risk overlay unavailable.</p>
          <button
            type="button"
            className={styles.retryBtn}
            onClick={() => { void refetchRiskProfiles(); }}
          >
            Retry risk overlay
          </button>
        </div>
      )}

      {showRiskLayer && <div className={styles.legend}>
        <h4 className={styles.legendTitle}>Regional risk profile</h4>
        {RISK_LABELS.map(({ label, swatch }) => (
          <div className={styles.legendRow} key={label}>
            <div className={styles.legendLabel}>
              <span className={`${styles.swatch} ${styles[swatch]}`} />
              <span>{label}</span>
            </div>
          </div>
        ))}
      </div>}

    </main>
  );
}
