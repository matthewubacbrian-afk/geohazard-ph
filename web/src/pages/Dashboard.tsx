import { useState } from 'react';
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

const navItems = [
  'Dashboard',
  'How It Works',
  'About',
  'Data Sources',
  'Contact',
];

type RiskLevelKey = 'high' | 'medium' | 'low';

type DashboardProps = {
  onNavigate?: (view: View) => void;
  onSettings?: () => void;
};

export default function Dashboard({ onNavigate, onSettings }: DashboardProps) {
  const [source, setSource] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [minMagnitude, setMinMagnitude] = useState(1);
  const [selectedEvent, setSelectedEvent] = useState<HazardEvent | null>(null);
  const realtime = useRealtimeAlerts();
  const { data: events = [], isLoading, error, refetch } = useEvents({
    source,
    since: startDate ? `${startDate}T00:00:00Z` : undefined,
    until: endDate ? `${endDate}T23:59:59.999Z` : undefined,
    minMagnitude,
  });

  const [basemap, setBasemap] = useState<BasemapId>('streets');
  const [activeView, setActiveView] = useState<DashboardView>('map');
  const [activeLayers, setActiveLayers] = useState<Record<string, boolean>>({
    events: true,
    risk: false,
  });
  const [activeRiskLevels, setActiveRiskLevels] = useState<RiskLevelKey[]>([
    'high',
    'medium',
    'low',
  ]);

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
          onBasemapChange={setBasemap}
          activeView={activeView}
          onViewChange={setActiveView}
          activeLayers={activeLayers}
          onToggleLayer={toggleLayer}
          activeRiskLevels={activeRiskLevels}
          onToggleRiskLevel={toggleRiskLevel}
          startDate={startDate}
          endDate={endDate}
          onStartDateChange={setStartDate}
          onEndDateChange={setEndDate}
          minMagnitude={minMagnitude}
          onMinMagnitudeChange={setMinMagnitude}
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
          onViewDetailedReport={() => setActiveView('risk')}
        />

        <section className={styles.sidePanel} aria-label="Activity panel">
          <RealtimeStatus {...realtime} />
          <EventFilterBar source={source} onChange={setSource} />
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
