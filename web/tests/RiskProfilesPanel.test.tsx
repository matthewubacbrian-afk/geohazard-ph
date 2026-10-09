import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import RiskProfilesPanel from '../src/components/risk/RiskProfilesPanel';
import { useRiskProfiles } from '../src/hooks/useRiskProfiles';

vi.mock('../src/hooks/useRiskProfiles');

const profiles = [
  {
    region_name: 'Bicol Region', cluster: 2, label: 'High', confidence: 0.82,
    feature_importances: { event_count: 0.42 }, model_version: 'v-test',
    generated_at: '2026-08-27T00:00:00Z', dataset_snapshot: 'Fixture',
  },
  {
    region_name: 'Palawan', cluster: 0, label: 'Low', confidence: 0.91,
    feature_importances: { event_count: 0.39 }, model_version: 'v-test',
    generated_at: '2026-08-27T00:00:00Z', dataset_snapshot: 'Fixture',
  },
];

describe('RiskProfilesPanel region lookup', () => {
  beforeEach(() => {
    vi.mocked(useRiskProfiles).mockReturnValue({
      data: profiles, isLoading: false, error: null, refetch: vi.fn(),
    } as unknown as ReturnType<typeof useRiskProfiles>);
  });

  it('filters lookup rows and profile cards from the loaded profiles', () => {
    render(<RiskProfilesPanel />);
    const input = screen.getByRole('searchbox', { name: 'Filter regions' });
    expect(screen.getByLabelText('Filter regions')).toBe(input);
    expect(screen.getByText('Filter regions', { selector: 'label' })).toBeVisible();
    fireEvent.change(input, { target: { value: 'pal' } });

    const results = screen.getByRole('list', { name: 'Matching regions' });
    expect(within(results).getByText('Palawan')).toBeInTheDocument();
    expect(within(results).queryByText('Bicol Region')).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Palawan' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Bicol Region' })).not.toBeInTheDocument();
    expect(screen.getByText('Risk profiles are descriptive statistics, not earthquake predictions.')).toBeInTheDocument();
  });

  it('shows no-match feedback and restores all results when the query is cleared', () => {
    render(<RiskProfilesPanel />);
    const input = screen.getByRole('searchbox', { name: 'Filter regions' });
    fireEvent.change(input, { target: { value: 'nowhere' } });
    expect(screen.getByText('No regions match your search.')).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Palawan' })).not.toBeInTheDocument();

    fireEvent.change(input, { target: { value: '' } });
    expect(screen.getByRole('heading', { name: 'Palawan' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Bicol Region' })).toBeInTheDocument();
  });

  it('normalizes search and risk labels consistently across display locales', () => {
    const originalToLocaleLowerCase = String.prototype.toLocaleLowerCase;
    const localeSpy = vi.spyOn(String.prototype, 'toLocaleLowerCase').mockImplementation(
      function (this: string) { return originalToLocaleLowerCase.call(this, 'tr'); },
    );
    vi.mocked(useRiskProfiles).mockReturnValue({
      data: [{ ...profiles[0], region_name: 'ISLAND', label: 'HIGH' }],
      isLoading: false, error: null, refetch: vi.fn(),
    } as unknown as ReturnType<typeof useRiskProfiles>);

    try {
      render(<RiskProfilesPanel />);
      fireEvent.change(document.querySelector('#risk-region-filter')!, { target: { value: 'i' } });
      const cardHeading = screen.getByRole('heading', { name: 'ISLAND' });
      expect(cardHeading).toBeInTheDocument();
      expect(cardHeading.closest('article')?.querySelector('[data-risk]')).toHaveAttribute('data-risk', 'high');
      expect(within(screen.getByRole('list', { name: 'Matching regions' })).getByRole('listitem'))
        .toHaveAttribute('data-risk', 'high');
    } finally {
      localeSpy.mockRestore();
    }
  });
});
