import { describe, expect, it } from 'vitest';

import { getDatePresetRange } from '../src/lib/dashboardFilterPresets';

describe('dashboard date presets', () => {
  it.each([
    ['7d', '2026-10-08'],
    ['30d', '2026-09-15'],
    ['90d', '2026-07-17'],
  ] as const)('calculates an inclusive %s UTC day window ending today', (preset, startDate) => {
    expect(getDatePresetRange(preset, new Date('2026-10-14T10:00:00Z'))).toEqual({
      startDate,
      endDate: '2026-10-14',
    });
  });
});
