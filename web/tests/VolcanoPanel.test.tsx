import { cleanup, render, screen, fireEvent } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import VolcanoPanel from '../src/components/volcanoes/VolcanoPanel';
import { useVolcanoes } from '../src/hooks/useVolcanoes';

vi.mock('../src/hooks/useVolcanoes');
afterEach(cleanup);
describe('VolcanoPanel', () => {
  it('shows loading and retryable source failure', () => {
    const refetch = vi.fn();
    vi.mocked(useVolcanoes).mockReturnValue({ isLoading: true, data: undefined, error: null, refetch } as unknown as ReturnType<typeof useVolcanoes>);
    const view = render(<VolcanoPanel />);
    expect(screen.getByText(/Loading volcano/)).toBeTruthy();
    vi.mocked(useVolcanoes).mockReturnValue({ isLoading: false, data: undefined, error: new Error('source'), refetch } as unknown as ReturnType<typeof useVolcanoes>);
    view.rerender(<VolcanoPanel />);
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(refetch).toHaveBeenCalled();
  });
  it('shows official level zero, source links and stale status without inventing an issue date', () => {
    vi.mocked(useVolcanoes).mockReturnValue({ isLoading: false, error: null, data: [{
      id: 'phivolcs:pinatubo', name: 'Pinatubo', current_alert_level: 0,
      source: 'phivolcs', source_url: 'https://wovodat.phivolcs.dost.gov.ph/bulletin/list-of-bulletin',
      stale: true, retrieved_at: '2026-09-08T00:00:00Z', bulletin_at: null, bulletin_url: null,
      latitude: null, longitude: null,
    }] } as unknown as ReturnType<typeof useVolcanoes>);
    render(<VolcanoPanel />);
    expect(screen.getByText('Alert Level 0')).toBeTruthy();
    expect(screen.getByText(/Cached source/)).toBeTruthy();
    expect(screen.getByRole('link', { name: /PHIVOLCS/ }).getAttribute('href')).toContain('phivolcs');
    expect(screen.getByText(/Bulletin date not supplied/)).toBeTruthy();
  });
  it('shows a clear empty state', () => {
    vi.mocked(useVolcanoes).mockReturnValue({ isLoading: false, data: [], error: null } as unknown as ReturnType<typeof useVolcanoes>);
    render(<VolcanoPanel />);
    expect(screen.getByText(/No volcano bulletins/)).toBeTruthy();
  });
});
