import { useMemo, useState } from 'react';
import { useRiskProfiles } from '../../hooks/useRiskProfiles';
import Skeleton from '../common/Skeleton';
import RegionLookup from './RegionLookup';
import RiskProfileCard from './RiskProfileCard';
import styles from './RiskProfilesPanel.module.css';

export default function RiskProfilesPanel() {
  const { data: profiles, isLoading, error, refetch } = useRiskProfiles();
  const [query, setQuery] = useState('');
  const loadedProfiles = profiles ?? [];
  const normalizedQuery = query.trim().toLowerCase();
  const filtered = useMemo(
    () => loadedProfiles.filter((profile) =>
      profile.region_name.toLowerCase().includes(normalizedQuery),
    ),
    [loadedProfiles, normalizedQuery],
  );

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>Regional risk profiles</h2>
          <p className={styles.subtitle}>Clustered by ML model</p>
        </div>
      </div>

      <div className={styles.body}>
        {isLoading && (
          <div className={styles.loading}>
            {[0, 1].map((i) => (
              <div key={i} className={styles.loadingCard}>
                <Skeleton width="60%" height={16} />
                <Skeleton width="30%" height={24} />
                <Skeleton width="100%" height={40} />
              </div>
            ))}
          </div>
        )}

        {!isLoading && error && (
          <div className={styles.error} role="alert">
            <p className={styles.errorText}>Failed to load risk profiles.</p>
            <button type="button" className={styles.retry} onClick={() => refetch()}>
              Retry
            </button>
          </div>
        )}

        {!isLoading && !error && loadedProfiles.length > 0 && (
          <>
            <div className={styles.lookupSection}>
              <label className={styles.searchLabel} htmlFor="risk-region-filter">Filter regions</label>
              <input
                id="risk-region-filter"
                className={styles.searchInput}
                type="search"
                aria-label="Filter regions"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search loaded regions"
              />
              <RegionLookup profiles={loadedProfiles} query={query} />
            </div>
            {filtered.length > 0 ? filtered.map((profile) => (
              <RiskProfileCard key={profile.region_name} profile={profile} />
            )) : <p className={styles.noResults}>No regions match your search.</p>}
          </>
        )}

        {!isLoading && !error && loadedProfiles.length === 0 && (
          <p className={styles.empty}>No risk profiles available.</p>
        )}
      </div>
    </div>
  );
}
