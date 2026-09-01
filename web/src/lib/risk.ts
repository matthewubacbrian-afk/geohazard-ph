export type RiskBucket = 'critical' | 'elevated' | 'baseline';

const KNOWN: Record<string, RiskBucket | undefined> = {
  critical: 'critical',
  high: 'critical',
  elevated: 'elevated',
  major: 'elevated',
  moderate: 'elevated',
  baseline: 'baseline',
  low: 'baseline',
  minor: 'baseline',
  normal: 'baseline',
};

export function eventRiskBucket(alertLevel?: string | null): RiskBucket {
  if (!alertLevel || typeof alertLevel !== 'string') return 'baseline';
  return KNOWN[alertLevel.toLowerCase().trim()] ?? 'baseline';
}
