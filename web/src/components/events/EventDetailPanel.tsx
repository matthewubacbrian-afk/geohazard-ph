import type { HazardEvent } from '../../types/hazard';
import { eventRiskBucket } from '../../lib/risk';
import styles from './EventDetailPanel.module.css';

type EventDetailPanelProps = {
  event: HazardEvent;
  onClose: () => void;
};

export default function EventDetailPanel({ event, onClose }: EventDetailPanelProps) {
  const bucket = eventRiskBucket(event.alert_level);

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <div>
          <p className={styles.title}>{event.place_name}</p>
          <span className={`${styles[`pill--${bucket}`]}`}>
            {bucket === 'critical' ? 'Critical' : bucket === 'elevated' ? 'Elevated' : 'Baseline'}
          </span>
        </div>
        <button type="button" className={styles.close} onClick={onClose} aria-label="Close detail">
          <span className="material-symbols-outlined" aria-hidden="true">
            close
          </span>
        </button>
      </div>

      <dl className={styles.grid}>
        {event.magnitude != null && (
          <>
            <dt className={styles.label}>Magnitude</dt>
            <dd className={styles.value}>{event.magnitude.toFixed(1)}</dd>
          </>
        )}
        {event.depth_km != null && (
          <>
            <dt className={styles.label}>Depth</dt>
            <dd className={styles.value}>{event.depth_km} km</dd>
          </>
        )}
        <dt className={styles.label}>Occurred</dt>
        <dd className={styles.value}>{new Date(event.occurred_at).toLocaleString()}</dd>
        <dt className={styles.label}>Coordinates</dt>
        <dd className={styles.value}>
          {event.latitude.toFixed(3)}, {event.longitude.toFixed(3)}
        </dd>
        <dt className={styles.label}>Type</dt>
        <dd className={styles.value}>{event.hazard_type}</dd>
      </dl>

      <p className={styles.source}>Source: {event.source}</p>
    </div>
  );
}
