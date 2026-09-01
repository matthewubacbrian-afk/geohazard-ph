import type { RiskProfile } from '../../types/hazard';
import styles from './RiskProfileCard.module.css';

type RiskProfileCardProps = {
  profile: RiskProfile;
};

export default function RiskProfileCard({ profile }: RiskProfileCardProps) {
  const sortedDrivers = Object.entries(profile.feature_importances).sort(
    ([, a], [, b]) => b - a,
  );

  return (
    <article className={styles.card}>
      <div className={styles.header}>
        <h3 className={styles.name}>{profile.region_name}</h3>
        <span className={styles.label}>{profile.label}</span>
      </div>

      <div className={styles.confidence}>
        <span className={styles.confidenceValue}>
          {Math.round(profile.confidence * 100)}%
        </span>
        <span className={styles.confidenceCaption}>confidence</span>
      </div>

      <div className={styles.drivers}>
        <strong className={styles.driversTitle}>Key drivers</strong>
        <ul className={styles.driverList}>
          {sortedDrivers.map(([key, value]) => (
            <li key={key} className={styles.driverRow}>
              <span className={styles.driverName}>{key}</span>
              <div className={styles.driverBarTrack}>
                <div
                  className={styles.driverBar}
                  style={{ width: `${Math.round(value * 100)}%` }}
                />
              </div>
              <span className={styles.driverValue}>{Math.round(value * 100)}%</span>
            </li>
          ))}
        </ul>
      </div>

      <p className={styles.metadata}>
        Model: {profile.model_version} | {profile.dataset_snapshot}
      </p>
      <p className={styles.disclaimer}>
        Statistical profiling based on historical records, not prediction.
      </p>
    </article>
  );
}
