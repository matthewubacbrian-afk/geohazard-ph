import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import LandslideOverlayStatus from '../src/components/map/LandslideOverlayStatus';

describe('LandslideOverlayStatus', () => {
  it('shows the loading state', () => {
    render(<LandslideOverlayStatus state="loading" onRetry={vi.fn()} />);

    expect(screen.getByRole('status')).toHaveTextContent(/loading NASA landslide susceptibility reference/i);
  });

  it('offers retry when NASA imagery fails', () => {
    const onRetry = vi.fn();
    render(<LandslideOverlayStatus state="error" onRetry={onRetry} />);

    expect(screen.getByRole('alert')).toHaveTextContent(/NASA landslide susceptibility reference unavailable/i);
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it('credits NASA and labels the legend as informational rather than an early warning', () => {
    render(<LandslideOverlayStatus state="ready" onRetry={vi.fn()} />);

    const source = screen.getByRole('link', { name: /NASA Global Landslide Susceptibility Map/i });
    expect(source).toHaveAttribute('href', expect.stringContaining('d9c8e1279e3e48c2ab3dd318a6649b3a'));
    expect(screen.getByText('Low · 0')).toBeInTheDocument();
    expect(screen.getByText('High · 5')).toBeInTheDocument();
    expect(screen.getByText(/coarse, informational susceptibility reference for awareness/i)).toBeInTheDocument();
    expect(screen.getByText(/not an early-warning authority or site-level assessment/i)).toBeInTheDocument();
    expect(screen.getByText(/may be research-grade and unsuitable for operational use/i)).toBeInTheDocument();
  });
});
