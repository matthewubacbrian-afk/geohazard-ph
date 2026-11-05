import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import RegionalActivityPanel from '../src/components/activity/RegionalActivityPanel';

describe('regional activity panel', () => {
  it('explains empty regions without implying low risk', () => {
    render(<RegionalActivityPanel events={[]} isLoading={false} error={null} />);
    expect(screen.getByRole('heading', { name: 'Regional earthquake activity' })).toBeVisible();
    expect(screen.getByText('No matching earthquake records.', { exact: false })).toBeVisible();
    fireEvent.click(screen.getByText('Coverage and limitations'));
    expect(screen.getByText(/No matching records does not mean no risk/)).toBeVisible();
    expect(screen.getAllByText(/0 recorded earthquakes/)).toHaveLength(17);
  });
  it('keeps loading and source failures distinct from an empty catalog', () => {
    const view = render(<RegionalActivityPanel events={[]} isLoading error={null} />);
    expect(screen.getByRole('status')).toHaveTextContent('Loading');
    expect(screen.queryByText(/0 recorded earthquakes/)).toBeNull();
    view.rerender(<RegionalActivityPanel events={[]} isLoading={false} error={new Error()} />);
    expect(screen.getByRole('alert')).toHaveTextContent('Activity unavailable');
    expect(screen.queryByText(/0 recorded earthquakes/)).toBeNull();
  });
});
