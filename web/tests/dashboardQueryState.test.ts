import { describe, expect, it } from 'vitest';

import {
  DEFAULT_DASHBOARD_QUERY,
  parseDashboardQuery,
  serializeDashboardQuery,
} from '../src/lib/dashboardQueryState';

describe('dashboard query state', () => {
  it('uses defaults when the query string is empty', () => {
    expect(parseDashboardQuery('')).toEqual(DEFAULT_DASHBOARD_QUERY);
  });

  it('round trips supported dashboard controls', () => {
    const state = parseDashboardQuery(
      '?view=risk&source=phivolcs&start=2026-01-01&end=2026-02-01&minMagnitude=4.5&basemap=terrain',
    );

    expect(state).toMatchObject({
      view: 'risk',
      source: 'phivolcs',
      startDate: '2026-01-01',
      endDate: '2026-02-01',
      minMagnitude: 4.5,
      basemap: 'terrain',
    });
    expect(parseDashboardQuery(serializeDashboardQuery(state))).toEqual(state);
  });

  it('ignores invalid values and omits defaults from serialized URLs', () => {
    expect(parseDashboardQuery('?view=unknown&minMagnitude=abc&basemap=unknown')).toEqual(
      DEFAULT_DASHBOARD_QUERY,
    );
    expect(serializeDashboardQuery(DEFAULT_DASHBOARD_QUERY)).toBe('');
  });
});