import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import RiskProfileCard from '../src/components/risk/RiskProfileCard';
import RegionLookup from '../src/components/risk/RegionLookup';
import type { RiskProfile } from '../src/types/hazard';

const profiles: RiskProfile[] = [
  {
    region_name: 'Bicol Region',
    cluster: 2,
    label: 'High',
    confidence: 0.82,
    feature_importances: { event_count: 0.42, max_magnitude: 0.31 },
    model_version: 'v-test',
    generated_at: '2026-08-27T00:00:00Z',
    dataset_snapshot: 'Kaggle fixture',
  },
  {
    region_name: 'Palawan',
    cluster: 0,
    label: 'Low',
    confidence: 0.91,
    feature_importances: { event_count: 0.39 },
    model_version: 'v-test',
    generated_at: '2026-08-27T00:00:00Z',
    dataset_snapshot: 'Kaggle fixture',
  },
];

describe('Risk profile components', () => {
  it('renders risk label confidence and feature drivers', () => {
    const html = renderToStaticMarkup(<RiskProfileCard profile={profiles[0]} />);

    expect(html).toContain('Bicol Region');
    expect(html).toContain('High');
    expect(html).toContain('82%');
    expect(html).toContain('event_count');
  });

  it('filters region lookup by query', () => {
    const html = renderToStaticMarkup(<RegionLookup profiles={profiles} query="pal" />);

    expect(html).toContain('Palawan');
    expect(html).not.toContain('Bicol Region');
  });
});
