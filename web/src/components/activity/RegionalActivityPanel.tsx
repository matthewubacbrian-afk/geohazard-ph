import { useMemo } from 'react';
import type { HazardEvent } from '../../types/hazard';
import { PHILIPPINE_REGIONS } from '../../data/philippine-regions';
import { buildRegionalActivity } from '../map/regionalActivity';
import styles from '../risk/RiskProfilesPanel.module.css';
import cards from '../risk/RiskProfileCard.module.css';
import activityStyles from './RegionalActivityPanel.module.css';

type Props = { events: HazardEvent[]; isLoading: boolean; error: Error | null };

export default function RegionalActivityPanel({ events, isLoading, error }: Props) {
  const activity = useMemo(() => buildRegionalActivity(events, PHILIPPINE_REGIONS), [events]);
  return <section className={styles.panel} aria-label="Regional earthquake activity">
    <div className={styles.header}><div>
      <h2 className={styles.title}>Regional earthquake activity</h2>
      <p className={styles.subtitle}>Recorded events · selected filters</p>
    </div></div>
    <div className={styles.body}>
      {isLoading ? <p className={styles.empty} role="status">Loading earthquake records…</p> : error
        ? <div className={styles.error}><p className={styles.errorText} role="alert">Activity unavailable. Retry loading events on the map.</p></div> : <>
          <div className={activityStyles.summary}>
          <p>Recorded earthquake counts for the selected filters.</p>
          <p>Observed record dates (UTC): {activity.firstOccurredAt
            ? `${activity.firstOccurredAt.slice(0, 10)} to ${activity.lastOccurredAt!.slice(0, 10)}`
            : 'No matching earthquake records.'}</p>
          <p>{activity.unassignedCount} offshore or outside-boundary records are not assigned
            to a region. {activity.invalidCount} invalid records excluded.</p>
          <details className={activityStyles.coverage}>
          <summary>Coverage and limitations</summary>
          <p>Shading shows earthquake epicenters inside regional boundaries. Counts reflect
            available records and reporting coverage, not seismic risk or a forecast.</p>
          <p>Source counts use each earthquake’s selected primary catalog record; they do
            not establish catalog completeness. No matching records does not mean no risk.</p>
          <p>Uses the pinned 17-region boundary snapshot; administrative boundaries may change.</p>
          </details>
          </div>
          <ul className={activityStyles.regions}>
            {activity.regions.map((region) => <li key={region.name}>
              <article className={cards.card}>
              <div className={activityStyles.regionHeader}>
                <h3 className={cards.name}>{region.name}</h3>
                <span className={activityStyles.count}>{region.count} recorded earthquakes</span>
              </div>
              {region.firstOccurredAt && <p className={cards.metadata}>UTC: {region.firstOccurredAt.slice(0, 10)} to {region.lastOccurredAt!.slice(0, 10)}</p>}
              <p className={cards.metadata}>{region.count ? Object.entries(region.sources)
                .map(([source, count]) => `${source.toUpperCase()}: ${count}`).join(' · ')
                : 'Insufficient data to characterize activity for these filters.'}</p>
              </article>
            </li>)}
          </ul>
        </>}
    </div>
  </section>;
}
