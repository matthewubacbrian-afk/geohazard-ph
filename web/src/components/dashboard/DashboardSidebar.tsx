import { useState } from 'react';
import Icon, { type IconName } from '../common/Icon';
import styles from './DashboardSidebar.module.css';
import { BASEMAPS, BASEMAP_IDS, type BasemapId } from '../map/basemaps';
import type { RiskBucket } from '../../lib/risk';

export type DashboardView = 'map' | 'filters' | 'history' | 'risk' | 'volcanoes';

const VIEWS: { key: DashboardView; label: string; icon: IconName }[] = [
  { key: 'map', label: 'Map', icon: 'map' },
  { key: 'filters', label: 'Seismic filters', icon: 'filter' },
  { key: 'history', label: 'Historical data', icon: 'history' },
  { key: 'volcanoes', label: 'Volcano bulletins', icon: 'volcano' },
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
  { key: 'faults', label: 'Fault lines', available: true },
  { key: 'volcanoes', label: 'Volcano zones', available: true },
];

const EVENT_CATEGORIES: { key: RiskBucket; label: string }[] = [
  { key: 'critical', label: 'Critical events' },
  { key: 'elevated', label: 'Elevated events' },
  { key: 'baseline', label: 'Baseline events' },
];

type DashboardSidebarProps = {
  basemap: BasemapId;
  onBasemapChange: (basemap: BasemapId) => void;
  activeView: DashboardView;
  onViewChange: (view: DashboardView) => void;
  activeLayers: Record<string, boolean>;
  onToggleLayer: (key: string) => void;
  activeEventCategories: RiskBucket[];
  onToggleEventCategory: (level: RiskBucket) => void;
  startDate: string;
  endDate: string;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
  minMagnitude: number;
  onMinMagnitudeChange: (magnitude: number) => void;
};

export default function DashboardSidebar({
  basemap,
  onBasemapChange,
  activeView,
  onViewChange,
  activeLayers,
  onToggleLayer,
  activeEventCategories,
  onToggleEventCategory,
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  minMagnitude,
  onMinMagnitudeChange,
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
                <Icon name={view.icon} className={styles.icon} />
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
              <Icon name="layers" className={styles.icon} />
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
          <h3 className={styles.sectionTitle}>Event feed categories</h3>
          <div className={styles.checklist}>
            {EVENT_CATEGORIES.map((level) => (
              <label key={level.key} className={styles.checkItem}>
                <input
                  type="checkbox"
                  checked={activeEventCategories.includes(level.key)}
                  onChange={() => onToggleEventCategory(level.key)}
                />
                <span>{level.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Date range</h3>
          <div className={styles.dateGrid}>
            <input
              type="date"
              value={startDate}
              onChange={(event) => onStartDateChange(event.target.value)}
              className={styles.input}
              aria-label="Start date"
            />
            <input
              type="date"
              value={endDate}
              onChange={(event) => onEndDateChange(event.target.value)}
              className={styles.input}
              aria-label="End date"
            />
          </div>
        </div>

        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>
            <span>Magnitude</span>
            <span className={styles.sectionValue}>{minMagnitude.toFixed(1)} - 9.0</span>
          </h3>
          <input
            type="range"
            aria-label="Minimum magnitude"
            min="1"
            max="9"
            step="0.1"
            value={minMagnitude}
            onChange={(event) => onMinMagnitudeChange(Number(event.target.value))}
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
