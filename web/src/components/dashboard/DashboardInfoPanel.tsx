import { useState } from 'react';
import { useEventSummary } from '../../hooks/useEventSummary';
import Icon from '../common/Icon';
import Skeleton from '../common/Skeleton';
import styles from './DashboardInfoPanel.module.css';

type DashboardInfoPanelProps = {
  onViewDetailedReport: () => void;
};

export default function DashboardInfoPanel({ onViewDetailedReport }: DashboardInfoPanelProps) {
  const [isVisible, setIsVisible] = useState(true);
  const { data: summary, isLoading, error, refetch } = useEventSummary();

  if (!isVisible) return null;

  return (
    <section className={styles.panel} aria-label="Regional summary and data note">
      <header className={styles.header}>
        <div>
          <h3 className={styles.title}>Earthquake activity</h3>
          <p className={styles.subtitle}>Philippines situational overview</p>
        </div>
        <button
          type="button"
          className={styles.close}
          aria-label="Close regional summary"
          onClick={() => setIsVisible(false)}
        >
          <Icon name="close" />
        </button>
      </header>

      <p className={styles.description}>
        The map shows events reported by selected sources. Marker size represents reported magnitude
        where available; map layers add geographic context.
      </p>

      {isLoading ? (
        <div className={styles.stats} role="status" aria-label="Loading event summary">
          <Skeleton width="38%" height={12} />
          <Skeleton width="24%" height={18} />
        </div>
      ) : error ? (
        <div className={styles.summaryState} role="alert">
          <p>Regional summary unavailable.</p>
          <button type="button" className={styles.retry} onClick={() => { void refetch(); }}>
            Retry summary
          </button>
        </div>
      ) : !summary ? (
        <p className={styles.summaryState}>No regional summary available.</p>
      ) : (
        <div className={styles.stats}>
          <div className={`${styles.stat} ${styles.statWide}`}>
            <span className={styles.marker} aria-hidden="true" />
            <div>
              <span className={styles.statLabel}>Classification</span>
              <strong>Coming soon</strong>
            </div>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Average magnitude</span>
            <strong>{summary.avg_magnitude != null ? summary.avg_magnitude.toFixed(2) : '—'}</strong>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Events in area</span>
            <strong>{summary.event_count.toLocaleString()}</strong>
          </div>
          <div className={`${styles.stat} ${styles.statFull}`}>
            <span className={styles.statLabel}>Dominant fault system</span>
            <strong>Coming soon</strong>
          </div>
        </div>
      )}

      <div className={styles.disclaimer}>
        <span className={styles.disclaimerMark} aria-hidden="true">i</span>
        <p>
          This public information dashboard supports situational awareness. Event data come from
          external sources and may be revised. This is not an official PHIVOLCS/NDRRMC warning or
          forecast.
        </p>
      </div>

      <footer className={styles.footer}>
        <button type="button" onClick={onViewDetailedReport}>View Detailed Report</button>
      </footer>
    </section>
  );
}
