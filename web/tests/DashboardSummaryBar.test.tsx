import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import DashboardSummaryBar from '../src/components/dashboard/DashboardSummaryBar';

const events = [
  { id: 'one' },
  { id: 'two' },
] as never[];

describe('DashboardSummaryBar', () => {
  it('shows the number of filtered events represented in the map', () => {
    render(<DashboardSummaryBar events={events} isLoading={false} error={null} />);

    expect(screen.getByRole('status')).toHaveTextContent('2 events in view');
  });

  it('keeps loading and error states visible in the map badge', () => {
    const { rerender } = render(<DashboardSummaryBar events={[]} isLoading error={null} />);
    expect(screen.getByRole('status')).toHaveTextContent('Loading events');

    rerender(<DashboardSummaryBar events={[]} isLoading={false} error={new Error('offline')} />);
    expect(screen.getByRole('status')).toHaveTextContent('Events unavailable');
  });
});
