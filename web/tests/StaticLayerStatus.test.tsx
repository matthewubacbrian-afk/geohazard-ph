import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import StaticLayerStatus from '../src/components/map/StaticLayerStatus';

describe('StaticLayerStatus', () => {
  it('shows loading, empty and error states with retry', () => {
    const retry = vi.fn();
    const view = render(<StaticLayerStatus label="Fault lines" loading rows={undefined} error={null} onRetry={retry} />);
    expect(screen.getByRole('status')).toHaveTextContent(/loading fault lines/i);
    view.rerender(<StaticLayerStatus label="Fault lines" loading={false} rows={[]} error={null} onRetry={retry} />);
    expect(screen.getByText(/no fault lines imported/i)).toBeInTheDocument();
    view.rerender(<StaticLayerStatus label="Fault lines" loading={false} rows={[]} error={new Error()} onRetry={retry} />);
    fireEvent.click(screen.getByRole('button', {name: 'Retry'}));
    expect(retry).toHaveBeenCalledOnce();
  });
  it('attributes imported features to their source and version', () => {
    render(<StaticLayerStatus label="Fault lines" loading={false} error={null} onRetry={vi.fn()} rows={[{
      id: '1', external_id: '1', name: 'Test', source: 'gem', source_url: 'https://example.org/data',
      license_name: 'CC-BY-SA-4.0', dataset_version: 'v1', imported_at: '2026-09-10T00:00:00Z',
      source_properties: {}, geometry: {type: 'LineString', coordinates: [[121, 14], [122, 15]]},
    }]} />);
    expect(screen.getByRole('link', {name: 'GEM'})).toHaveAttribute('href', 'https://example.org/data');
    expect(screen.getByText(/v1.*CC-BY-SA/)).toBeInTheDocument();
  });
});
