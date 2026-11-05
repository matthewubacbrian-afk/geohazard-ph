import { useMemo } from 'react';
import type { HazardEvent } from '../../types/hazard';
import { PHILIPPINE_REGIONS } from '../../data/philippine-regions';
import { buildRegionalActivity } from '../map/regionalActivity';
import styles from '../risk/RiskProfilesPanel.module.css';

type Props = { events: HazardEvent[]; isLoading: boolean; error: Error | null };

export default function RegionalActivityPanel({ events, isLoading, error }: Props) {
  const activity = useMemo(() => buildRegionalActivity(events, PHILIPPINE_REGIONS), [events]);
  return <section className={styles.panel} aria-label="Regional earthquake activity">
    <div className={styles.header}><div>
      <h2 className={styles.title}>Regional earthquake activity</h2>
      <p className={styles.subtitle}>Recorded events · selected filters</p>
    </div></div>
    <div className={styles.body}>
      {isLoading ? <p role="status">Loading earthquake records…</p> : error
        ? <p role="alert">Activity unavailable. Retry loading events on the map.</p> : <>
          <p>Shading shows earthquake epicenters inside regional boundaries. Counts reflect
            available records and reporting coverage, not seismic risk or a forecast.</p>
          <p>Observed record dates (UTC): {activity.firstOccurredAt
            ? `${activity.firstOccurredAt.slice(0, 10)} to ${activity.lastOccurredAt!.slice(0, 10)}`
            : 'No matching earthquake records.'}</p>
          <p>{activity.unassignedCount} offshore or outside-boundary records are not assigned
            to a region. {activity.invalidCount} invalid records excluded.</p>
          <p>Source counts use each earthquake’s selected primary catalog record; they do
            not establish catalog completeness. No matching records does not mean no risk.</p>
          <p>Uses the pinned 17-region boundary snapshot; administrative boundaries may change.</p>
          <ul>
            {activity.regions.map((region) => <li key={region.name}>
              <strong>{region.name}: {region.count} recorded earthquakes</strong>
              {region.firstOccurredAt && <p>UTC: {region.firstOccurredAt.slice(0, 10)} to {region.lastOccurredAt!.slice(0, 10)}</p>}
              <p>{region.count ? Object.entries(region.sources)
                .map(([source, count]) => `${source.toUpperCase()}: ${count}`).join(' · ')
                : 'Insufficient data to characterize activity for these filters.'}</p>
            </li>)}
          </ul>
        </>}
    </div>
  </section>;
}
