import type { RiskProfile } from '../../types/hazard';
import styles from './RegionLookup.module.css';

interface RegionLookupProps {
  profiles: RiskProfile[];
  query: string;
}

export default function RegionLookup({ profiles, query }: RegionLookupProps) {
  const normalizedQuery = query.trim().toLowerCase();
  const filtered = profiles.filter((p) =>
    p.region_name.toLowerCase().includes(normalizedQuery)
  );

  return (
    <div className={styles.lookup}>
      <ul aria-label="Matching regions">
        {filtered.map((profile) => (
          <li className={styles.row} key={profile.region_name} data-risk={profile.label.toLowerCase()}>
            <span className={styles.regionName}>{profile.region_name}</span>
            <span className={styles.riskLabel}>{profile.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
