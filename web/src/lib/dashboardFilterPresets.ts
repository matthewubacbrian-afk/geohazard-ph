export type DashboardDatePreset = '1d' | '7d' | '30d' | '90d';

const PRESET_DAYS: Record<DashboardDatePreset, number> = {
  '1d': 1,
  '7d': 7,
  '30d': 30,
  '90d': 90,
};

export function getDatePresetRange(
  preset: DashboardDatePreset,
  now = new Date(),
): { startDate: string; endDate: string } {
  const end = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  const start = new Date(end);
  start.setUTCDate(start.getUTCDate() - PRESET_DAYS[preset] + 1);

  return {
    startDate: start.toISOString().slice(0, 10),
    endDate: end.toISOString().slice(0, 10),
  };
}
