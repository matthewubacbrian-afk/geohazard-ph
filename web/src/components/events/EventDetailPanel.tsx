import type { HazardEvent } from '../../types/hazard';

type EventDetailPanelProps = {
  event?: HazardEvent;
};

export default function EventDetailPanel({ event }: EventDetailPanelProps) {
  if (!event) {
    return <aside className="panel">Select an event to inspect details.</aside>;
  }

  return <aside className="panel">{event.place_name}</aside>;
}
