import { useState } from 'react';
import styles from './DashboardSidebar.module.css';
import { BASEMAPS, BASEMAP_IDS, type BasemapId } from '../map/basemaps';

export type DashboardView = 'map' | 'filters' | 'history' | 'risk';

const VIEWS: { key: DashboardView; label: string; icon: string }[] = [
  { key: 'map', label: 'Map', icon: 'map' },
  { key: 'filters', label: 'Seismic filters', icon: 'filter_alt' },
  { key: 'history', label: 'Historical data', icon: 'history' },
  { key: 'risk', label: 'Risk reports', icon: 'assessment' },
];

type LayerDef = {
  key: string;
  label: string;
  available: boolean;
};

const LAYERS: LayerDef[] = [
  { key: 'events', label: 'Live events', available: true },
  { key: 'risk', label: 'Risk overlay', available: true },
  { key: 'faults', label: 'Fault lines', available: false },
  { key: 'volcanoes', label: 'Volcano zones', available: false },
];

type RiskLevelKey = 'high' | 'medium' | 'low';

const RISK_LEVELS: { key: RiskLevelKey; label: string; swatch: string }[] = [
  { key: 'high', label: 'High Risk', swatch: styles['swatch--high'] },
  { key: 'medium', label: 'Moderate Risk', swatch: styles['swatch--medium'] },
  { key: 'low', label: 'Low Risk', swatch: styles['swatch--low'] },
];

type DashboardSidebarProps = {
  basemap: BasemapId;
  onBasemapChange: (basemap: BasemapId) => void;
  activeView: DashboardView;
  onViewChange: (view: DashboardView) => void;
  activeLayers: Record<string, boolean>;
  onToggleLayer: (key: string) => void;
  activeRiskLevels: RiskLevelKey[];
  onToggleRiskLevel: (level: RiskLevelKey) => void;
};

export default function DashboardSidebar({
  basemap,
  onBasemapChange,
  activeView,
  onViewChange,
  activeLayers,
  onToggleLayer,
  activeRiskLevels,
  onToggleRiskLevel,
}: DashboardSidebarProps) {
  const [layersOpen, setLayersOpen] = useState(false);

  return (
    <aside className={styles.sidebar} aria-label="Risk controls panel">
      <div className={styles.header}>
        <h2 className={styles.title}>Controls</h2>
        <p className={styles.subtitle}>LGU Assessment Tools</p>
      </div>

      <div className={styles.body}>
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Views</h3>
          <div className={styles.tabList}>
            {VIEWS.map((view) => (
              <button
                key={view.key}
                type="button"
                className={`${styles.tab} ${activeView === view.key ? styles.tabActive : ''}`}
                aria-current={activeView === view.key ? 'true' : undefined}
                onClick={() => onViewChange(view.key)}
              >
                <span className={styles.icon} aria-hidden="true">
                  {view.icon}
                </span>
                <span>{view.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Map layers</h3>
          <div className={styles.dropdown}>
            <button
              type="button"
              className={styles.dropdownTrigger}
              aria-expanded={layersOpen}
              aria-label={`Map Layers: ${BASEMAPS[basemap].label}`}
              onClick={() => setLayersOpen((open) => !open)}
            >
              <span className={styles.icon} aria-hidden="true">
                layers
              </span>
              <span>{BASEMAPS[basemap].label}</span>
              <span className={styles.caret} aria-hidden="true">
                ▾
              </span>
            </button>
            {layersOpen && (
              <ul className={styles.dropdownMenu} role="menu">
                {BASEMAP_IDS.map((id) => (
                  <li key={id}>
                    <button
                      type="button"
                      className={`${styles.dropdownItem} ${
                        id === basemap ? styles.dropdownItemActive : ''
                      }`}
                      role="menuitem"
                      aria-pressed={id === basemap}
                      onClick={() => {
                        onBasemapChange(id);
                        setLayersOpen(false);
                      }}
                    >
                      <span>{BASEMAPS[id].label}</span>
                      {id === basemap && (
                        <span className={styles.check} aria-hidden="true">
                          ✓
                        </span>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className={styles.layerList}>
            {LAYERS.map((layer) => (
              <label
                key={layer.key}
                className={`${styles.layerItem} ${
                  layer.available ? '' : styles.layerItemDisabled
                }`}
              >
                <input
                  type="checkbox"
                  checked={!!activeLayers[layer.key]}
                  disabled={!layer.available}
                  onChange={() => onToggleLayer(layer.key)}
                  className={styles.layerInput}
                />
                <span className={styles.layerLabelWrapper}>
                  <span>{layer.label}</span>
                  {!layer.available && (
                    <span className={styles.soonTag}>Soon</span>
                  )}
                </span>
              </label>
            ))}
          </div>
        </div>

        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Risk level</h3>
          <div className={styles.checklist}>
            {RISK_LEVELS.map((level) => (
              <label key={level.key} className={styles.checkItem}>
                <input
                  type="checkbox"
                  checked={activeRiskLevels.includes(level.key)}
                  onChange={() => onToggleRiskLevel(level.key)}
                />
                <span className={`${styles.swatch} ${level.swatch}`} />
                <span>{level.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Date range</h3>
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
      </div>
    </aside>
  );
}
