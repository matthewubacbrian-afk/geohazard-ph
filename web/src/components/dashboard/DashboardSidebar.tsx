import Icon, { type IconName } from '../common/Icon';
import styles from './DashboardSidebar.module.css';
import { BASEMAPS, BASEMAP_IDS, type BasemapId } from '../map/basemaps';
import type { RiskBucket } from '../../lib/risk';
import type { HazardEvent } from '../../types/hazard';
import { getDatePresetRange, type DashboardDatePreset } from '../../lib/dashboardFilterPresets';
import EventFilterBar from '../events/EventFilterBar';

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
  { key: 'landslideSusceptibility', label: 'Landslide susceptibility', available: true },
];

const EVENT_CATEGORIES: { key: RiskBucket; label: string }[] = [
  { key: 'critical', label: 'Critical events' },
  { key: 'elevated', label: 'Elevated events' },
  { key: 'baseline', label: 'Baseline events' },
];

const HAZARD_TYPES: { key: HazardEvent['hazard_type']; label: string }[] = [
  { key: 'earthquake', label: 'Earthquake' },
  { key: 'volcanic', label: 'Volcano activity' },
  { key: 'landslide', label: 'Other hazards' },
];

const DATE_PRESETS: { key: DashboardDatePreset; label: string }[] = [
  { key: '1d', label: '1D' },
  { key: '7d', label: '7D' },
  { key: '30d', label: '30D' },
  { key: '90d', label: '90D' },
];

const MAGNITUDE_PRESETS = [
  { value: 1, label: 'All' },
  { value: 2.5, label: '≥ 2.5' },
  { value: 4, label: '≥ 4.0' },
  { value: 5, label: '≥ 5.0' },
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
  activeHazardTypes: HazardEvent['hazard_type'][];
  onToggleHazardType: (type: HazardEvent['hazard_type']) => void;
  onDatePresetChange: (preset: DashboardDatePreset) => void;
  source: string;
  onSourceChange: (source: string) => void;
  collapsed: boolean;
  onToggleCollapsed: () => void;
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
  activeHazardTypes,
  onToggleHazardType,
  onDatePresetChange,
  source,
  onSourceChange,
  collapsed,
  onToggleCollapsed,
}: DashboardSidebarProps) {
  if (collapsed) {
    return <aside className={`${styles.sidebar} ${styles.collapsed}`} aria-label="Risk controls panel">
      <button type="button" className={styles.railToggle} aria-label="Expand controls" onClick={onToggleCollapsed}>
        <Icon name="layers" />
      </button>
      <div className={styles.railViews}>{VIEWS.map((view) => <button key={view.key} type="button"
        className={`${styles.railButton} ${activeView === view.key ? styles.railActive : ''}`}
        aria-label={`Open ${view.label}`} title={view.label} onClick={() => { onViewChange(view.key); onToggleCollapsed(); }}>
        <Icon name={view.icon} />
      </button>)}</div>
    </aside>;
  }
  return (
    <aside className={styles.sidebar} aria-label="Risk controls panel">
      <div className={styles.header}>
        <h2 className={styles.title}>Controls</h2>
        <p className={styles.subtitle}>LGU Assessment Tools</p>
        <button type="button" className={styles.collapseButton} aria-label="Collapse controls" onClick={onToggleCollapsed}>‹</button>
      </div>

      <div className={styles.body}>
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Map view</h3>
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
          <div className={styles.basemapGroup}>
            <span className={styles.subheading}>Basemap</span>
            <div className={styles.basemapOptions} role="group" aria-label="Basemap">
              {BASEMAP_IDS.map((id) => (
                <button
                  key={id}
                  type="button"
                  className={`${styles.basemapOption} ${id === basemap ? styles.basemapActive : ''}`}
                  aria-pressed={id === basemap}
                  onClick={() => onBasemapChange(id)}
                >
                  {BASEMAPS[id].label}
                </button>
              ))}
            </div>
          </div>

          <div className={styles.layerList} role="group" aria-label="Map layers">
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
          <h3 className={styles.sectionTitle}>Time window</h3>
          <div className={styles.datePresets} role="group" aria-label="Date window presets">
            {DATE_PRESETS.map(({ key, label }) => {
              const range = getDatePresetRange(key);
              const selected = startDate === range.startDate && endDate === range.endDate;
              return (
                <button
                  key={key}
                  type="button"
                  className={`${styles.preset} ${selected ? styles.presetActive : ''}`}
                  aria-pressed={selected}
                  onClick={() => onDatePresetChange(key)}
                >
                  {label}
                </button>
              );
            })}
          </div>
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
          <h3 className={styles.sectionTitle}>Event filters</h3>
          <EventFilterBar source={source} onChange={onSourceChange} />
          <h4 className={styles.subheading}>Magnitude (M)</h4>
          <div className={styles.magnitudePresets} role="group" aria-label="Magnitude presets">
            {MAGNITUDE_PRESETS.map(({ value, label }) => (
              <button
                key={value}
                type="button"
                className={`${styles.magnitudePreset} ${minMagnitude === value ? styles.presetActive : ''}`}
                aria-pressed={minMagnitude === value}
                onClick={() => onMinMagnitudeChange(value)}
              >
                {label}
              </button>
            ))}
          </div>
          <h4 className={styles.subheading}>Event type</h4>
          <div className={styles.checklist}>
            {HAZARD_TYPES.map(({ key, label }) => (
              <label key={key} className={styles.checkItem}>
                <input
                  type="checkbox"
                  checked={activeHazardTypes.includes(key)}
                  onChange={() => onToggleHazardType(key)}
                />
                <span>{label}</span>
              </label>
            ))}
          </div>
          <h4 className={styles.subheading}>Risk category</h4>
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
          <span className={styles.sectionValue}>{minMagnitude.toFixed(1)} minimum</span>
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
