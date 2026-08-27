import EventFilterBar from '../events/EventFilterBar';
import LayerControls from '../map/LayerControls';
import VolcanoAlertCard from '../volcano/VolcanoAlertCard';

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <EventFilterBar />
      <LayerControls />
      <VolcanoAlertCard />
    </aside>
  );
}
