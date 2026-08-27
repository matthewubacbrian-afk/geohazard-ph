import type { HazardEvent } from '../../types/hazard';

type EventMarkerProps = {
  event: HazardEvent;
};

export default function EventMarker({ event }: EventMarkerProps) {
  return <span title={event.place_name}>M{event.magnitude ?? 'n/a'}</span>;
}
