import type { HazardEvent } from '../../types/hazard';

type EventListProps = {
  events: HazardEvent[];
};

export default function EventList({ events }: EventListProps) {
  return (
    <div className="panel">
      <h2>Recent Events</h2>
      <ul>
        {events.map((event) => (
          <li key={event.id}>
            <strong>{event.place_name}</strong>
            <span>{event.source.toUpperCase()}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
