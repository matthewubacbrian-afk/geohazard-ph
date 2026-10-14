import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import EventFilterBar from '../src/components/events/EventFilterBar';

describe('EventFilterBar', () => {
  it('shows the active source and wires each source button to the existing callback', () => {
    const onChange = vi.fn();
    render(<EventFilterBar source="phivolcs" onChange={onChange} />);

    expect(screen.getByRole('button', { name: 'PHIVOLCS' })).toHaveAttribute('aria-pressed', 'true');
    fireEvent.click(screen.getByRole('button', { name: 'USGS' }));

    expect(onChange).toHaveBeenCalledWith('usgs');
  });
});
