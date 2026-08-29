import MapView from "../map/MapView";
import type { HazardEvent } from "../../types/hazard";

type DashboardMapAreaProps = {
  events: HazardEvent[];
};

export default function DashboardMapArea({ events }: DashboardMapAreaProps) {
  return (
    <main className="dashboard-map-area" aria-label="Geospatial risk dashboard map">
      <MapView events={events} />

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
            <div className="dashboard-stat-marker dashboard-stat-marker--high" />
            <div>
              <span className="dashboard-stat-label">Classification</span>
              <strong className="dashboard-stat-value dashboard-stat-value--high">
                Critical Risk
              </strong>
            </div>
          </div>

          <div className="dashboard-stat">
            <span className="dashboard-stat-label">Avg Magnitude</span>
            <strong className="dashboard-stat-value">
              5.2<span> Mw</span>
            </strong>
          </div>

          <div className="dashboard-stat">
            <span className="dashboard-stat-label">Frequency (YTD)</span>
            <strong className="dashboard-stat-value">
              14<span> events</span>
            </strong>
          </div>

          <div className="dashboard-stat dashboard-stat--full">
            <span className="dashboard-stat-label">Dominant Fault System</span>
            <div className="dashboard-fault-box">
              Philippine Fault Zone (Digdig Fault)
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
