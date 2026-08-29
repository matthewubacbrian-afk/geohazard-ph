import MapView from "../map/MapView";
import type { HazardEvent } from "../../types/hazard";
import { useEventSummary } from "../../hooks/useEventSummary";

type DashboardMapAreaProps = {
  events: HazardEvent[];
  isLoading: boolean;
  error: Error | null;
  onRetry: () => void;
};

export default function DashboardMapArea({
  events,
  isLoading,
  error,
  onRetry,
}: DashboardMapAreaProps) {
  const {
    data: summary,
    isLoading: summaryLoading,
    error: summaryError,
  } = useEventSummary();

  const avgMagnitude = !summaryLoading && !summaryError && summary?.avg_magnitude != null
    ? summary.avg_magnitude
    : null;
  const eventCount = !summaryLoading && !summaryError && summary?.event_count != null
    ? summary.event_count
    : null;

  return (
    <main className="dashboard-map-area" aria-label="Geospatial risk dashboard map">
      {isLoading && !error ? (
        <div className="dashboard-events-status">Loading events…</div>
      ) : error ? (
        <div className="dashboard-events-status dashboard-events-status--error">
          <p>Failed to load events.</p>
          <button type="button" onClick={onRetry}>
            Retry
          </button>
        </div>
      ) : (
        <MapView events={events} />
      )}

      <div className="dashboard-map-legend">
        <h4>Seismic Risk Level</h4>
        <div className="dashboard-legend-row">
          <div className="dashboard-legend-label">
            <span className="dashboard-swatch dashboard-swatch--high" />
            <span>Critical</span>
          </div>
          <span className="dashboard-legend-value">PGA &gt; 0.4g</span>
        </div>
        <div className="dashboard-legend-row">
          <div className="dashboard-legend-label">
            <span className="dashboard-swatch dashboard-swatch--medium" />
            <span>Elevated</span>
          </div>
          <span className="dashboard-legend-value">PGA 0.2-0.4g</span>
        </div>
        <div className="dashboard-legend-row">
          <div className="dashboard-legend-label">
            <span className="dashboard-swatch dashboard-swatch--low" />
            <span>Baseline</span>
          </div>
          <span className="dashboard-legend-value">PGA &lt; 0.2g</span>
        </div>
      </div>

      <div className="dashboard-map-controls" aria-label="Map controls">
        <button type="button" aria-label="Zoom in">
          <span className="material-symbols-outlined">add</span>
        </button>
        <button type="button" aria-label="Zoom out">
          <span className="material-symbols-outlined">remove</span>
        </button>
        <button
          type="button"
          aria-label="My location"
          className="dashboard-map-control--stacked"
        >
          <span className="material-symbols-outlined">my_location</span>
        </button>
        <button type="button" aria-label="Explore">
          <span className="material-symbols-outlined">explore</span>
        </button>
      </div>

      <div className="dashboard-floating-card">
        <div className="dashboard-floating-header">
          <div>
            <h3>Cagayan Valley</h3>
            <p>Region II</p>
          </div>
          <button type="button" aria-label="Close panel">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <div className="dashboard-stat-grid">
          <div className="dashboard-stat dashboard-stat--wide">
            <div className="dashboard-stat-marker" />
            <div>
              <span className="dashboard-stat-label">Classification</span>
              <strong className="dashboard-stat-value">
                Not available
              </strong>
            </div>
          </div>

          <div className="dashboard-stat">
            <span className="dashboard-stat-label">Avg Magnitude</span>
            <strong className="dashboard-stat-value">
              {avgMagnitude != null ? `${avgMagnitude}` : '—'}<span> Mw</span>
            </strong>
          </div>

          <div className="dashboard-stat">
            <span className="dashboard-stat-label">Frequency (YTD)</span>
            <strong className="dashboard-stat-value">
              {eventCount != null ? `${eventCount}` : '—'}
              {eventCount != null ? <span> events</span> : null}
            </strong>
          </div>

          <div className="dashboard-stat dashboard-stat--full">
            <span className="dashboard-stat-label">Dominant Fault System</span>
            <div className="dashboard-fault-box">
              Not available
            </div>
          </div>
        </div>

        <div className="dashboard-card-footer">
          <button type="button">View Detailed Report</button>
        </div>
      </div>
    </main>
  );
}
