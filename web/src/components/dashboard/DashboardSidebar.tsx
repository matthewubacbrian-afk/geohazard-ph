import styles from "./DashboardSidebar.module.css";

const tabs = [
  { label: "Map Layers", icon: "layers", active: false },
  { label: "Seismic Filters", icon: "filter_alt", active: true },
  { label: "Historical Data", icon: "history", active: false },
  { label: "Risk Reports", icon: "assessment", active: false },
];

export default function DashboardSidebar() {
  return (
    <aside className={styles.sidebar} aria-label="Risk controls panel">
      <div className={styles.header}>
        <h2 className={styles.title}>Risk Controls</h2>
        <p className={styles.subtitle}>LGU Assessment Tools</p>
      </div>

      <div className={styles.body}>
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Date Range</h3>
          <div className={styles.dateGrid}>
            <input type="date" defaultValue="2023-01-01" className={styles.input} />
            <input type="date" defaultValue="2024-01-01" className={styles.input} />
          </div>
        </div>

        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>
            <span>Magnitude</span>
            <span className={styles.sectionValue}>4.0 - 9.0</span>
          </h3>
          <input
            type="range"
            min="1"
            max="9"
            step="0.1"
            defaultValue={4}
            className={styles.range}
          />
          <div className={styles.scale}>
            <span>M1</span>
            <span>M5</span>
            <span>M9</span>
          </div>
        </div>

        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Risk Level</h3>
          <div className={styles.checklist}>
            <label className={styles.checkItem}>
              <input type="checkbox" defaultChecked />
              <span className={`${styles.swatch} ${styles["swatch--high"]}`} />
              <span>High Risk</span>
            </label>
            <label className={styles.checkItem}>
              <input type="checkbox" defaultChecked />
              <span className={`${styles.swatch} ${styles["swatch--medium"]}`} />
              <span>Moderate Risk</span>
            </label>
            <label className={styles.checkItem}>
              <input type="checkbox" />
              <span className={`${styles.swatch} ${styles["swatch--low"]}`} />
              <span>Low Risk</span>
            </label>
          </div>
        </div>

        <div className={`${styles.section} ${styles.tabsSection}`}>
          <h3 className={styles.sectionTitle}>Views</h3>
          <div className={styles.tabList}>
            {tabs.map((tab) => (
              <button
                key={tab.label}
                type="button"
                className={`${styles.tab} ${tab.active ? styles.tabActive : ""}`}
                aria-current={tab.active ? "true" : undefined}
              >
                <span className={styles.icon} aria-hidden="true">
                  {tab.icon}
                </span>
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}
