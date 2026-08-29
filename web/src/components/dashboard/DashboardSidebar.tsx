const tabs = [
  { label: "Map Layers", icon: "layers", active: false },
  { label: "Seismic Filters", icon: "filter_alt", active: true },
  { label: "Historical Data", icon: "history", active: false },
  { label: "Risk Reports", icon: "assessment", active: false },
];

export default function DashboardSidebar() {
  return (
    <aside className="dashboard-sidebar" aria-label="Risk controls panel">
      <div className="dashboard-sidebar-header">
        <h2>Risk Controls</h2>
        <p>LGU Assessment Tools</p>
      </div>

      <div className="dashboard-sidebar-body">
        <div className="dashboard-section">
          <h3>Date Range</h3>
          <div className="dashboard-date-grid">
            <input type="date" defaultValue="2023-01-01" className="dashboard-input" />
            <input type="date" defaultValue="2024-01-01" className="dashboard-input" />
          </div>
        </div>

        <div className="dashboard-section">
          <h3>
            <span>Magnitude</span>
            <span className="dashboard-section-value">4.0 - 9.0</span>
          </h3>
          <input
            type="range"
            min="1"
            max="9"
            step="0.1"
            defaultValue={4}
            className="dashboard-range"
          />
          <div className="dashboard-scale">
            <span>M1</span>
            <span>M5</span>
            <span>M9</span>
          </div>
        </div>

        <div className="dashboard-section">
          <h3>Risk Level</h3>
          <div className="dashboard-checklist">
            <label className="dashboard-check-item">
              <input type="checkbox" defaultChecked />
              <span className="dashboard-swatch dashboard-swatch--high" />
              <span>High Risk</span>
            </label>
            <label className="dashboard-check-item">
              <input type="checkbox" defaultChecked />
              <span className="dashboard-swatch dashboard-swatch--medium" />
              <span>Moderate Risk</span>
            </label>
            <label className="dashboard-check-item">
              <input type="checkbox" />
              <span className="dashboard-swatch dashboard-swatch--low" />
              <span>Low Risk</span>
            </label>
          </div>
        </div>

        <div className="dashboard-section dashboard-section--tabs">
          <h3>Views</h3>
          <div className="dashboard-tab-list">
            {tabs.map((tab) => (
              <a
                key={tab.label}
                href="#"
                className={`dashboard-tab ${tab.active ? "dashboard-tab--active" : ""}`}
              >
                <span className="material-symbols-outlined" aria-hidden="true">
                  {tab.icon}
                </span>
                <span>{tab.label}</span>
              </a>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}
