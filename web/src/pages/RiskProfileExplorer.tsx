import { useState } from 'react';
import { useRiskProfiles } from '../hooks/useRiskProfiles';
import RiskProfileCard from '../components/risk/RiskProfileCard';
import RegionLookup from '../components/risk/RegionLookup';

export default function RiskProfileExplorer() {
  const { data: profiles = [] } = useRiskProfiles();
  const [query, setQuery] = useState('');

  return (
    <section className="risk-profile-explorer">
      <h2>Regional Risk Profiles</h2>
      <input
        type="text"
        placeholder="Filter by region..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <RegionLookup profiles={profiles} query={query} />
      <div className="profile-cards">
        {profiles.map((profile) => (
          <RiskProfileCard key={profile.region_name} profile={profile} />
        ))}
      </div>
    </section>
  );
}
