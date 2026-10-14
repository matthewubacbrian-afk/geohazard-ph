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
import type { View } from '../types/views';
import type { BasemapId } from '../components/map/basemaps';
import VolcanoPanel from '../components/volcanoes/VolcanoPanel';
import RealtimeStatus from '../components/dashboard/RealtimeStatus';
import DashboardInfoPanel from '../components/dashboard/DashboardInfoPanel';
import { useRealtimeAlerts } from '../hooks/useRealtimeAlerts';
import { useNotifications } from '../hooks/useNotifications';
import DashboardActivityPanel, { type ActivityTab } from '../components/dashboard/DashboardActivityPanel';
import NotificationCenter from '../components/dashboard/NotificationCenter';
import { useEvents } from '../hooks/useEvents';
import { eventRiskBucket, type RiskBucket } from '../lib/risk';
import type { HazardEvent } from '../types/hazard';
import { getDatePresetRange, type DashboardDatePreset } from '../lib/dashboardFilterPresets';
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
];

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
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [activeHazardTypes, setActiveHazardTypes] = useState<HazardEvent['hazard_type'][]>([
    'earthquake',
    'volcanic',
    'landslide',
  ]);
  const notificationState = useNotifications();
  const realtime = useRealtimeAlerts(notificationState.addEvent);
  const [controlsCollapsed, setControlsCollapsed] = useState(false);
  const [activityCollapsed, setActivityCollapsed] = useState(false);
  const [activityTab, setActivityTab] = useState<ActivityTab>('events');
  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return;
    const media = window.matchMedia('(max-width: 900px)');
    const expandForSmallScreens = () => {
      if (media.matches) { setControlsCollapsed(false); setActivityCollapsed(false); }
    };
    expandForSmallScreens();
    media.addEventListener('change', expandForSmallScreens);
    return () => media.removeEventListener('change', expandForSmallScreens);
  }, []);
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
  const [activeEventCategories, setActiveEventCategories] = useState<RiskBucket[]>([
    'critical',
    'elevated',
    'baseline',
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

  function toggleEventCategory(level: RiskBucket) {
    setActiveEventCategories((prev) =>
      prev.includes(level) ? prev.filter((l) => l !== level) : [...prev, level],
    );
  }

  function toggleHazardType(type: HazardEvent['hazard_type']) {
    setActiveHazardTypes((previous) =>
      previous.includes(type) ? previous.filter((item) => item !== type) : [...previous, type],
    );
  }

  const showRisk = activeView === 'risk';
  const visibleEvents = events.filter((event) => {
    if (!activeLayers.events) return false;
    return activeEventCategories.includes(eventRiskBucket(event.alert_level)) &&
      activeHazardTypes.includes(event.hazard_type);
  });
  const selectedEvent = visibleEvents.find((event) => event.id === selectedEventId) ?? null;

  useEffect(() => {
    if (selectedEventId && !selectedEvent) setSelectedEventId(null);
  }, [selectedEventId, selectedEvent]);

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

  function changeDatePreset(preset: DashboardDatePreset) {
    const range = getDatePresetRange(preset);
    setStartDate(range.startDate);
    setEndDate(range.endDate);
    updateQuery(range);
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
        status={<RealtimeStatus {...realtime} />}
        onNavigate={onNavigate}
        onSettings={onSettings}
      />

      <div className={`${styles.main} ${controlsCollapsed ? styles.controlsCollapsed : ''} ${activityCollapsed ? styles.activityCollapsed : ''}`}>
        <DashboardSidebar
          basemap={basemap}
          onBasemapChange={changeBasemap}
          activeView={activeView}
          onViewChange={changeView}
          activeLayers={activeLayers}
          onToggleLayer={toggleLayer}
          activeEventCategories={activeEventCategories}
          onToggleEventCategory={toggleEventCategory}
          startDate={startDate}
          endDate={endDate}
          onStartDateChange={changeStartDate}
          onEndDateChange={changeEndDate}
          minMagnitude={minMagnitude}
          onMinMagnitudeChange={changeMinMagnitude}
          activeHazardTypes={activeHazardTypes}
          onToggleHazardType={toggleHazardType}
          onDatePresetChange={changeDatePreset}
          source={source}
          onSourceChange={changeSource}
          collapsed={controlsCollapsed}
          onToggleCollapsed={() => setControlsCollapsed((value) => !value)}
        />

        <DashboardMapArea
          events={visibleEvents}
          isLoading={isLoading}
          error={error as Error | null}
          onRetry={() => refetch()}
          basemap={basemap}
          selectedEvent={selectedEvent}
          onSelectEvent={(event) => setSelectedEventId(event.id)}
          showEvents={activeLayers.events}
          showRiskLayer={activeLayers.risk}
          faults={faults.data}
          volcanoZones={volcanoZones.data}
          showFaults={activeLayers.faults}
          showVolcanoZones={activeLayers.volcanoes}
          volcanoOverlayRevision={volcanoOverlayRevision}
          onVolcanoOverlayState={setVolcanoOverlayState}
        />

        <DashboardActivityPanel collapsed={activityCollapsed} unreadCount={notificationState.unreadCount}
          activeTab={activityTab} onToggleCollapsed={() => setActivityCollapsed((value) => !value)}
          onSelectTab={(tab) => {
            setActivityTab(tab);
            if (tab === 'notifications' || tab === 'events') {
              setActiveView('map');
              updateQuery({ view: 'map' });
            }
          }}>
          <div className={styles.activityContent}>
          {activeLayers.faults && <StaticLayerStatus label="Fault lines" rows={faults.data}
            loading={faults.isLoading} error={faults.error} onRetry={() => { void faults.refetch(); }} />}
          {activeLayers.volcanoes && (volcanoZones.data?.length ?
            <StaticLayerStatus label="Volcano zones" rows={volcanoZones.data}
              loading={volcanoZones.isLoading} error={volcanoZones.error} onRetry={() => { void volcanoZones.refetch(); }} /> :
            <VolcanoOverlayStatus state={volcanoOverlayState}
              onRetry={() => setVolcanoOverlayRevision(value => value + 1)} />)}
          {activityTab === 'notifications' ? <NotificationCenter notifications={notificationState.notifications}
            onMarkRead={notificationState.markRead} onMarkAllRead={notificationState.markAllRead} /> : activeView === 'volcanoes' ? <VolcanoPanel /> : showRisk ? <RiskProfilesPanel /> : (
            <EventFeed
              events={visibleEvents}
              isLoading={isLoading}
              error={error as Error | null}
              onRetry={() => refetch()}
              selectedEvent={selectedEvent}
              onSelectEvent={(event) => setSelectedEventId(event.id)}
              onClearSelection={() => setSelectedEventId(null)}
            />
          )}
          {activityTab === 'events' && <DashboardInfoPanel onViewDetailedReport={() => changeView('risk')} />}
          </div>
        </DashboardActivityPanel>
      </div>
    </div>
  );
}
