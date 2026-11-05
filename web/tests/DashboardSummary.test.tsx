import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../src/components/map/MapView', () => ({
  default: () => <div aria-label="Hazard map" />,
}));
import DashboardMapArea from '../src/components/dashboard/DashboardMapArea';

describe('Dashboard recorded activity overlay', () => {
  it('shows count bins rather than risk labels', () => {
    render(<DashboardMapArea events={[]} isLoading={false} error={null} onRetry={vi.fn()} />);
    expect(screen.getByText('Recorded earthquakes')).toBeVisible();
    for (const label of ['No matching records', '1–9', '10–49', '50–99', '100+']) {
      expect(screen.getByText(label)).toBeVisible();
    }
    expect(screen.queryByText(/Very High|Regional risk profile/)).toBeNull();
  });
  it('shows the events failure and retry instead of a misleading empty-data legend', () => {
    const retry = vi.fn();
    render(<DashboardMapArea events={[]} isLoading={false} error={new Error()} onRetry={retry} />);
    expect(screen.queryByText('Recorded earthquakes')).toBeNull();
    screen.getByRole('button', { name: 'Retry' }).click();
    expect(retry).toHaveBeenCalledTimes(1);
  });
});
