import { useState } from 'react';
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
import EventFilterBar from '../components/events/EventFilterBar';
import RealtimeStatus from '../components/dashboard/RealtimeStatus';
import { useRealtimeAlerts } from '../hooks/useRealtimeAlerts';
import { useEvents } from '../hooks/useEvents';

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
};

export default function Dashboard({ onNavigate }: DashboardProps) {
  const [source, setSource] = useState('');
  const realtime = useRealtimeAlerts();
  const { data: events = [], isLoading, error, refetch } = useEvents(source);

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

  return (
    <div className={styles.page}>
      <TopNav
        items={navItems}
        activeItem="Dashboard"
        theme="dashboard"
        onNavigate={onNavigate}
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
        />

        <DashboardMapArea
          events={events}
          isLoading={isLoading}
          error={error as Error | null}
          onRetry={() => refetch()}
          basemap={basemap}
        />

        <section className={styles.sidePanel} aria-label="Activity panel">
          <RealtimeStatus {...realtime} />
          <EventFilterBar source={source} onChange={setSource} />
          {activeView === 'volcanoes' ? <VolcanoPanel /> : showRisk ? <RiskProfilesPanel /> : (
            <EventFeed
              events={events}
              isLoading={isLoading}
              error={error as Error | null}
              onRetry={() => refetch()}
            />
          )}
        </section>
      </div>
    </div>
  );
}
