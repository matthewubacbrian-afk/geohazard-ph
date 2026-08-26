import type { RiskProfile } from '../../types/hazard';

interface RiskProfileCardProps {
  profile: RiskProfile;
}

export default function RiskProfileCard({ profile }: RiskProfileCardProps) {
  const sortedDrivers = Object.entries(profile.feature_importances)
    .sort(([, a], [, b]) => b - a);

  return (
    <div className="risk-profile-card">
      <h3>{profile.region_name}</h3>
      <div className="risk-label">{profile.label}</div>
      <div className="confidence">{Math.round(profile.confidence * 100)}%</div>
      <div className="feature-drivers">
        <strong>Key drivers:</strong>
        <ul>
          {sortedDrivers.map(([key, value]) => (
            <li key={key}>
              {key}: {Math.round(value * 100)}%
            </li>
          ))}
        </ul>
      </div>
      <div className="metadata">
        <small>Model: {profile.model_version} | {profile.dataset_snapshot}</small>
      </div>
      <div className="disclaimer">
        <small>Statistical profiling based on historical records, not prediction.</small>
      </div>
    </div>
  );
}
