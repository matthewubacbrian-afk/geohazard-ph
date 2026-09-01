import { useRiskProfiles } from '../../hooks/useRiskProfiles';
import Skeleton from '../common/Skeleton';
import RiskProfileCard from './RiskProfileCard';
import styles from './RiskProfilesPanel.module.css';

export default function RiskProfilesPanel() {
  const { data: profiles, isLoading, error, refetch } = useRiskProfiles();

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <div>
          <p className={styles.title}>Regional risk profiles</p>
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

        {!isLoading && !error && profiles && profiles.length > 0 && (
          <>
            {profiles.map((profile) => (
              <RiskProfileCard key={profile.region_name} profile={profile} />
            ))}
          </>
        )}

        {!isLoading && !error && (!profiles || profiles.length === 0) && (
          <p className={styles.empty}>No risk profiles available.</p>
        )}
      </div>
    </div>
  );
}
