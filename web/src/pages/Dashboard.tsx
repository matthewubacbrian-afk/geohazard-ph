import { useStaticLayers } from '../hooks/useStaticLayers';
import StaticLayerStatus from '../components/map/StaticLayerStatus';
import VolcanoOverlayStatus from '../components/map/VolcanoOverlayStatus';
import type { VolcanoOverlayState } from '../components/map/volcanoOverlays';
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import styles from './Dashboard.module.css';
import DashboardMapArea from '../components/dashboard/DashboardMapArea';
import DashboardSidebar, {
  type DashboardView,
} from '../components/dashboard/DashboardSidebar';
import TopNav from '../components/layout/TopNav';
import EventFeed from '../components/events/EventFeed';
import RiskProfilesPanel from '../components/risk/RiskProfilesPanel';
import type { HazardEvent } from '../types/hazard';
import type { View } from '../types/views';
import type { BasemapId } from '../components/map/basemaps';
import VolcanoPanel from '../components/volcanoes/VolcanoPanel';
import EventFilterBar from '../components/events/EventFilterBar';
import RealtimeStatus from '../components/dashboard/RealtimeStatus';
import { useRealtimeAlerts } from '../hooks/useRealtimeAlerts';
import { useEvents } from '../hooks/useEvents';
import { eventRiskBucket } from '../lib/risk';
import {
  parseDashboardQuery,
  serializeDashboardQuery,
  type DashboardQueryState,
} from '../lib/dashboardQueryState';

const navItems = [
  'Dashboard',
  'How It Works',
  'About',
  'Data Sources',
  'Historical',
  'Contact',
];

type RiskLevelKey = 'high' | 'medium' | 'low';

type DashboardProps = {
  onNavigate?: (view: View) => void;
  onSettings?: () => void;
};

export default function Dashboard({ onNavigate, onSettings }: DashboardProps) {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = parseDashboardQuery(searchParams.toString());
  const [source, setSource] = useState(initialQuery.source);
  const [volcanoOverlayState, setVolcanoOverlayState] = useState<VolcanoOverlayState>('loading');
  const [volcanoOverlayRevision, setVolcanoOverlayRevision] = useState(0);
  const [startDate, setStartDate] = useState(initialQuery.startDate);
  const [endDate, setEndDate] = useState(initialQuery.endDate);
  const [minMagnitude, setMinMagnitude] = useState(initialQuery.minMagnitude);
  const [selectedEvent, setSelectedEvent] = useState<HazardEvent | null>(null);
  const realtime = useRealtimeAlerts();
  const { data: events = [], isLoading, error, refetch } = useEvents({
    source,
    since: startDate ? `${startDate}T00:00:00Z` : undefined,
    until: endDate ? `${endDate}T23:59:59.999Z` : undefined,
    minMagnitude,
  });

  const [basemap, setBasemap] = useState<BasemapId>(initialQuery.basemap);
  const [activeView, setActiveView] = useState<DashboardView>(initialQuery.view);
  const [activeLayers, setActiveLayers] = useState<Record<string, boolean>>({
    events: true,
    risk: false,
    faults: false,
    volcanoes: false,
  });
  const [activeRiskLevels, setActiveRiskLevels] = useState<RiskLevelKey[]>([
    'high',
    'medium',
    'low',
  ]);

  useEffect(() => {
    const query = parseDashboardQuery(searchParams.toString());
    setSource(query.source);
    setStartDate(query.startDate);
    setEndDate(query.endDate);
    setMinMagnitude(query.minMagnitude);
    setBasemap(query.basemap);
    setActiveView(query.view);
  }, [searchParams]);

  const faults = useStaticLayers('faults', Boolean(activeLayers.faults));
  const volcanoZones = useStaticLayers('volcano-zones', Boolean(activeLayers.volcanoes));

  function toggleLayer(key: string) {
    setActiveLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function toggleRiskLevel(level: RiskLevelKey) {
    setActiveRiskLevels((prev) =>
      prev.includes(level) ? prev.filter((l) => l !== level) : [...prev, level],
    );
  }

  const showRisk = activeView === 'risk';
  const visibleEvents = events.filter((event) => {
    if (!activeLayers.events) return false;
    const bucket = eventRiskBucket(event.alert_level);
    const riskLevel = bucket === 'critical' ? 'high' : bucket === 'elevated' ? 'medium' : 'low';
    return activeRiskLevels.includes(riskLevel);
  });

  function updateQuery(patch: Partial<DashboardQueryState>) {
    const next: DashboardQueryState = {
      view: activeView,
      source,
      startDate,
      endDate,
      minMagnitude,
      basemap,
      ...patch,
    };
    const query = serializeDashboardQuery(next);
    setSearchParams(query, { replace: true });
  }

  function changeView(view: DashboardView) {
    setActiveView(view);
    updateQuery({ view });
  }

  function changeSource(value: string) {
    setSource(value);
    updateQuery({ source: value });
  }

  function changeStartDate(value: string) {
    setStartDate(value);
    updateQuery({ startDate: value });
  }

  function changeEndDate(value: string) {
    setEndDate(value);
    updateQuery({ endDate: value });
  }

  function changeMinMagnitude(value: number) {
    setMinMagnitude(value);
    updateQuery({ minMagnitude: value });
  }

  function changeBasemap(value: BasemapId) {
    setBasemap(value);
    updateQuery({ basemap: value });
  }

  return (
    <div className={styles.page}>
      <TopNav
        items={navItems}
        activeItem="Dashboard"
        theme="dashboard"
        onNavigate={onNavigate}
        onSettings={onSettings}
      />

      <div className={styles.main}>
        <DashboardSidebar
          basemap={basemap}
          onBasemapChange={changeBasemap}
          activeView={activeView}
          onViewChange={changeView}
          activeLayers={activeLayers}
          onToggleLayer={toggleLayer}
          activeRiskLevels={activeRiskLevels}
          onToggleRiskLevel={toggleRiskLevel}
          startDate={startDate}
          endDate={endDate}
          onStartDateChange={changeStartDate}
          onEndDateChange={changeEndDate}
          minMagnitude={minMagnitude}
          onMinMagnitudeChange={changeMinMagnitude}
        />

        <DashboardMapArea
          events={visibleEvents}
          isLoading={isLoading}
          error={error as Error | null}
          onRetry={() => refetch()}
          basemap={basemap}
          selectedEvent={selectedEvent}
          showEvents={activeLayers.events}
          showRiskLayer={activeLayers.risk}
          faults={faults.data}
          volcanoZones={volcanoZones.data}
          showFaults={activeLayers.faults}
          showVolcanoZones={activeLayers.volcanoes}
          volcanoOverlayRevision={volcanoOverlayRevision}
          onVolcanoOverlayState={setVolcanoOverlayState}
          onViewDetailedReport={() => setActiveView('risk')}
        />

        <section className={styles.sidePanel} aria-label="Activity panel">
          {activeLayers.faults && <StaticLayerStatus label="Fault lines" rows={faults.data}
            loading={faults.isLoading} error={faults.error} onRetry={() => { void faults.refetch(); }} />}
          {activeLayers.volcanoes && (volcanoZones.data?.length ?
            <StaticLayerStatus label="Volcano zones" rows={volcanoZones.data}
              loading={volcanoZones.isLoading} error={volcanoZones.error} onRetry={() => { void volcanoZones.refetch(); }} /> :
            <VolcanoOverlayStatus state={volcanoOverlayState}
              onRetry={() => setVolcanoOverlayRevision(value => value + 1)} />)}
          <RealtimeStatus {...realtime} />
          <EventFilterBar source={source} onChange={changeSource} />
          {activeView === 'volcanoes' ? <VolcanoPanel /> : showRisk ? <RiskProfilesPanel /> : (
            <EventFeed
              events={visibleEvents}
              isLoading={isLoading}
              error={error as Error | null}
              onRetry={() => refetch()}
              onSelectEvent={(event) => setSelectedEvent({ ...event })}
            />
          )}
        </section>
      </div>
    </div>
  );
}
