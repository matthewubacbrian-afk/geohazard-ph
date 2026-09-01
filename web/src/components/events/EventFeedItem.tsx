import type { HazardEvent } from '../../types/hazard';
import { eventRiskBucket } from '../../lib/risk';
import styles from './EventFeedItem.module.css';

type EventFeedItemProps = {
  event: HazardEvent;
  selected: boolean;
  onSelect: (id: string) => void;
};

export default function EventFeedItem({ event, selected, onSelect }: EventFeedItemProps) {
  const bucket = eventRiskBucket(event.alert_level);

  return (
    <button
      type="button"
      className={`${styles.item} ${selected ? styles.itemSelected : ''}`}
      onClick={() => onSelect(event.id)}
      aria-pressed={selected}
    >
      <div className={styles.row}>
        <span className={styles.heading}>
          {event.magnitude != null ? (
            <span className={styles.magnitude}>M {event.magnitude.toFixed(1)}</span>
          ) : (
            'Alert'
          )}{' '}
          · {event.place_name}
        </span>
        <span className={`${styles[`pill--${bucket}`]}`}>
          {bucket === 'critical' ? 'Critical' : bucket === 'elevated' ? 'Elevated' : 'Baseline'}
        </span>
      </div>

      <div className={styles.meta}>
        {event.depth_km != null && <span>{event.depth_km}km depth</span>}
        <span>{new Date(event.occurred_at).toLocaleString()}</span>
        <span className={styles.source}>{event.source}</span>
      </div>
    </button>
  );
}
