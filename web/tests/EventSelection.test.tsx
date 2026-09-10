import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import Dashboard from '../src/pages/Dashboard';

const event = {
  id: 'e1', hazard_type: 'earthquake', source: 'usgs',
  latitude: 14.6, longitude: 120.97, place_name: 'Luzon earthquake',
  magnitude: 4.5, occurred_at: '2026-08-29T00:00:00Z',
};
vi.mock('../src/hooks/useStaticLayers', () => ({
  useStaticLayers: () => ({ data: [], isLoading: false, error: null, refetch: vi.fn() }),
}));
vi.mock('../src/hooks/useEvents', () => ({
  useEvents: () => ({ data: [event], isLoading: false, error: null, refetch: vi.fn() }),
}));
vi.mock('../src/hooks/useRealtimeAlerts', () => ({
  useRealtimeAlerts: () => ({ connected: true, lastUpdated: null }),
}));
vi.mock('../src/components/dashboard/DashboardMapArea', () => ({
  default: ({ selectedEvent }: { selectedEvent?: typeof event }) => (
    <div role="status">{selectedEvent ? `Map target: ${selectedEvent.longitude}, ${selectedEvent.latitude}` : 'No map target'}</div>
  ),
}));
afterEach(cleanup);
describe('activity selection', () => {
  it('sends the selected activity coordinates to the map while showing its details', () => {
    render(<Dashboard />);
    expect(screen.getByText('No map target')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /Luzon earthquake/i }));
    expect(screen.getByText('Map target: 120.97, 14.6')).toBeTruthy();
    expect(screen.getByRole('button', { name: /close/i })).toBeTruthy();
  });
});
