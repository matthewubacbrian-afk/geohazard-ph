import type { RiskProfile } from '../../types/hazard';

interface RegionLookupProps {
  profiles: RiskProfile[];
  query: string;
}

export default function RegionLookup({ profiles, query }: RegionLookupProps) {
  const filtered = profiles.filter((p) =>
    p.region_name.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="region-lookup">
      <ul>
        {filtered.map((profile) => (
          <li key={profile.region_name}>
            <span className="region-name">{profile.region_name}</span>
            <span className="risk-label">{profile.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
