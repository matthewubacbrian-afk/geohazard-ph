import EventList from '../components/events/EventList';
import Header from '../components/layout/Header';
import Sidebar from '../components/layout/Sidebar';
import MapView from '../components/map/MapView';
import { useEvents } from '../hooks/useEvents';
import RiskProfileExplorer from './RiskProfileExplorer';

export default function Dashboard() {
  const { data: events = [] } = useEvents();

  return (
    <main>
      <Header />
      <div className="workspace">
        <Sidebar />
        <MapView events={events} />
        <EventList events={events} />
        <RiskProfileExplorer />
      </div>
    </main>
  );
}
