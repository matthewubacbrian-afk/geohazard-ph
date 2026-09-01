import styles from "./DashboardMapArea.module.css";
import Skeleton from "../common/Skeleton";
import MapView from "../map/MapView";
import type { BasemapId } from "../map/basemaps";
import type { HazardEvent } from "../../types/hazard";
import { useEventSummary } from "../../hooks/useEventSummary";

type DashboardMapAreaProps = {
  events: HazardEvent[];
  isLoading: boolean;
  error: Error | null;
  onRetry: () => void;
  basemap?: BasemapId;
};

export default function DashboardMapArea({
  events,
  isLoading,
  error,
  onRetry,
  basemap = "streets",
}: DashboardMapAreaProps) {
  const {
    data: summary,
    isLoading: summaryLoading,
    error: summaryError,
  } = useEventSummary();

  const avgMagnitude =
    !summaryLoading && !summaryError && summary?.avg_magnitude != null
      ? summary.avg_magnitude
      : null;
  const eventCount =
    !summaryLoading && !summaryError && summary?.event_count != null
      ? summary.event_count
      : null;

  return (
    <main className={styles.mapArea} aria-label="Geospatial risk dashboard map">
      <MapView events={events} basemap={basemap} />

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

      <div className={styles.legend}>
        <h4 className={styles.legendTitle}>Seismic Risk Level</h4>
        <div className={styles.legendRow}>
          <div className={styles.legendLabel}>
            <span className={`${styles.swatch} ${styles["swatch--high"]}`} />
            <span>Critical</span>
          </div>
          <span className={styles.legendValue}>PGA &gt; 0.4g</span>
        </div>
        <div className={styles.legendRow}>
          <div className={styles.legendLabel}>
            <span className={`${styles.swatch} ${styles["swatch--medium"]}`} />
            <span>Elevated</span>
          </div>
          <span className={styles.legendValue}>PGA 0.2-0.4g</span>
        </div>
        <div className={styles.legendRow}>
          <div className={styles.legendLabel}>
            <span className={`${styles.swatch} ${styles["swatch--low"]}`} />
            <span>Baseline</span>
          </div>
          <span className={styles.legendValue}>PGA &lt; 0.2g</span>
        </div>
      </div>

      <div className={styles.controls} aria-label="Map controls">
        <button type="button" className={styles.controlBtn} aria-label="Zoom in">
          <span className="material-symbols-outlined" aria-hidden="true">
            add
          </span>
        </button>
        <button type="button" className={styles.controlBtn} aria-label="Zoom out">
          <span className="material-symbols-outlined" aria-hidden="true">
            remove
          </span>
        </button>
        <button
          type="button"
          className={`${styles.controlBtn} ${styles.controlBtnStacked}`}
          aria-label="My location"
        >
          <span className="material-symbols-outlined" aria-hidden="true">
            my_location
          </span>
        </button>
        <button type="button" className={styles.controlBtn} aria-label="Explore">
          <span className="material-symbols-outlined" aria-hidden="true">
            explore
          </span>
        </button>
      </div>

      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <div>
            <h3 className={styles.cardTitle}>Philippines</h3>
            <p className={styles.cardSub}>Regional activity</p>
          </div>
          <button type="button" className={styles.cardClose} aria-label="Close panel">
            <span className="material-symbols-outlined" aria-hidden="true">
              close
            </span>
          </button>
        </div>

        {summaryLoading ? (
          <div className={styles.statGrid}>
            <div className={`${styles.stat} ${styles.statWide}`}>
              <Skeleton width={16} height={46} />
              <div>
                <Skeleton width={90} height={10} />
                <Skeleton width={60} height={16} />
              </div>
            </div>
            <div className={styles.stat}>
              <Skeleton width={80} height={10} />
              <Skeleton width={44} height={20} />
            </div>
            <div className={styles.stat}>
              <Skeleton width={80} height={10} />
              <Skeleton width={44} height={20} />
            </div>
            <div className={`${styles.stat} ${styles.statFull}`}>
              <Skeleton width={120} height={10} />
              <Skeleton width="100%" height={40} />
            </div>
          </div>
        ) : (
          <div className={styles.statGrid}>
            <div className={`${styles.stat} ${styles.statWide}`}>
              <span className={styles.statMarker} />
              <div>
                <span className={styles.statLabel}>Classification</span>
                <strong className={styles.statValue}>
                  <span>Coming soon</span>
                </strong>
              </div>
            </div>

            <div className={styles.stat}>
              <span className={styles.statLabel}>Avg Magnitude</span>
              <strong className={styles.statValue}>
                {avgMagnitude != null ? `${avgMagnitude}` : "—"}
                {avgMagnitude != null ? <span> Mw</span> : null}
              </strong>
            </div>

            <div className={styles.stat}>
              <span className={styles.statLabel}>Frequency (YTD)</span>
              <strong className={styles.statValue}>
                {eventCount != null ? `${eventCount}` : "—"}
                {eventCount != null ? <span> events</span> : null}
              </strong>
            </div>

            <div className={`${styles.stat} ${styles.statFull}`}>
              <span className={styles.statLabel}>Dominant Fault System</span>
              <div className={styles.faultBox}>Coming soon</div>
            </div>
          </div>
        )}

        <div className={styles.cardFooter}>
          <button type="button">View Detailed Report</button>
        </div>
      </div>
    </main>
  );
}
