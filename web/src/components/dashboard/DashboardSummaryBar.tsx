import type { HazardEvent } from '../../types/hazard';
import styles from './DashboardSummaryBar.module.css';

type DashboardSummaryBarProps = {
  events: HazardEvent[];
  isLoading: boolean;
  error: Error | null;
};

export default function DashboardSummaryBar({ events, isLoading, error }: DashboardSummaryBarProps) {
  const message = isLoading
    ? 'Loading events'
    : error
      ? 'Events unavailable'
      : `${events.length.toLocaleString()} events in view`;

  return (
    <div className={styles.summary} role="status" aria-live="polite">
      <span className={styles.indicator} aria-hidden="true" />
      <span>{message}</span>
    </div>
  );
}
