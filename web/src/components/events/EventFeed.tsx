import { useMemo, useState } from 'react';
import type { HazardEvent } from '../../types/hazard';
import { eventRiskBucket, type RiskBucket } from '../../lib/risk';
import Skeleton from '../common/Skeleton';
import EventFeedItem from './EventFeedItem';
import EventDetailPanel from './EventDetailPanel';
import styles from './EventFeed.module.css';

type EventFeedProps = {
  events: HazardEvent[];
  isLoading: boolean;
  error: Error | null;
  onRetry: () => void;
  onSelectEvent?: (event: HazardEvent) => void;
  selectedEvent?: HazardEvent | null;
  onClearSelection?: () => void;
};

const BUCKETS: { key: RiskBucket; label: string }[] = [
  { key: 'critical', label: 'Critical' },
  { key: 'elevated', label: 'Elevated' },
  { key: 'baseline', label: 'Baseline' },
];

export default function EventFeed({
  events,
  isLoading,
  error,
  onRetry,
  onSelectEvent,
  selectedEvent = null,
  onClearSelection,
}: EventFeedProps) {
  const [activeBuckets, setActiveBuckets] = useState<RiskBucket[]>([
    'critical',
    'elevated',
    'baseline',
  ]);
  const filtered = useMemo(
    () => events.filter((e) => activeBuckets.includes(eventRiskBucket(e.alert_level))),
    [events, activeBuckets],
  );

  const remainingEvents = filtered.filter((event) => event.id !== selectedEvent?.id);

  function toggleBucket(bucket: RiskBucket) {
    setActiveBuckets((prev) =>
      prev.includes(bucket) ? prev.filter((b) => b !== bucket) : [...prev, bucket],
    );
  }

  return (
    <div className={styles.feed}>
      <div className={styles.header}>
        <div>
          <p className={styles.title}>Regional activity</p>
          <p className={styles.subtitle}>Live hazard events</p>
        </div>
        <span className={styles.count}>{filtered.length} events</span>
      </div>

      <div className={styles.filters}>
        {BUCKETS.map((bucket) => {
          const isActive = activeBuckets.includes(bucket.key);
          return (
            <button
              key={bucket.key}
              type="button"
              className={`${styles.pill} ${isActive ? styles.pillActive : ''}`}
              aria-pressed={isActive}
              onClick={() => toggleBucket(bucket.key)}
            >
              {bucket.label}
            </button>
          );
        })}
      </div>

      <div className={styles.body}>
        {selectedEvent && (
          <>
            <EventFeedItem
              event={selectedEvent}
              selected
              onSelect={() => onSelectEvent?.(selectedEvent)}
            />
            <EventDetailPanel event={selectedEvent} onClose={() => onClearSelection?.()} />
          </>
        )}

        {isLoading && (
          <div className={styles.loading} role="status" aria-label="Loading live events">
            {[0, 1, 2].map((i) => (
              <div key={i} className={styles.loadingRow}>
                <Skeleton width="55%" height={14} />
                <Skeleton width="30%" height={10} />
              </div>
            ))}
          </div>
        )}

        {!isLoading && error && (
          <div className={styles.error} role="alert">
            <p className={styles.errorText}>Failed to load events.</p>
            <button type="button" className={styles.retry} onClick={onRetry}>
              Retry
            </button>
          </div>
        )}

        {!isLoading && !error && !selectedEvent && filtered.length === 0 && (
          <p className={styles.empty}>No events match the current filters.</p>
        )}

        {!isLoading && !error &&
          remainingEvents.map((event) => (
            <EventFeedItem
              key={event.id}
              event={event}
              selected={false}
              onSelect={() => onSelectEvent?.(event)}
            />
          ))}
      </div>
    </div>
  );
}
