import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import Dashboard from '../src/pages/Dashboard';

const event = {
  id: 'e1', hazard_type: 'earthquake', source: 'usgs',
  latitude: 14.6, longitude: 120.97, place_name: 'Luzon earthquake',
  magnitude: 4.5, occurred_at: '2026-08-29T00:00:00Z',
};

const state = vi.hoisted(() => ({
  events: [] as Array<{
    id: string;
    hazard_type: string;
    source: string;
    latitude: number;
    longitude: number;
    place_name: string;
    magnitude: number;
    occurred_at: string;
  }>,
  selectOnMap: undefined as ((selected: typeof event) => void) | undefined,
}));

state.events = [event];
vi.mock('../src/hooks/useStaticLayers', () => ({
  useStaticLayers: () => ({ data: [], isLoading: false, error: null, refetch: vi.fn() }),
}));
vi.mock('../src/hooks/useEvents', () => ({
  useEvents: () => ({ data: state.events, isLoading: false, error: null, refetch: vi.fn() }),
}));
vi.mock('../src/hooks/useRealtimeAlerts', () => ({
  useRealtimeAlerts: () => ({ connected: true, lastUpdated: null }),
}));
vi.mock('../src/components/dashboard/DashboardMapArea', () => ({
  default: ({ selectedEvent, onSelectEvent }: {
    selectedEvent?: typeof event | null;
    onSelectEvent?: (selected: typeof event) => void;
  }) => {
    state.selectOnMap = onSelectEvent;
    return <div role="status">{selectedEvent ? `Map target: ${selectedEvent.id}` : 'No map target'}</div>;
  },
}));

afterEach(() => {
  cleanup();
  state.events = [event];
  state.selectOnMap = undefined;
});

function renderDashboard() {
  return render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>,
  );
}

describe('activity selection', () => {
  it('shares a map selection with the activity details and clears both when closed', () => {
    renderDashboard();

    expect(screen.getByText('No map target')).toBeTruthy();
    act(() => state.selectOnMap?.(event));
    expect(screen.getByText('Map target: e1')).toBeTruthy();
    expect(screen.getByText('Coordinates')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: /close/i }));
    expect(screen.getByText('No map target')).toBeTruthy();
    expect(screen.queryByText('Coordinates')).toBeNull();
  });

  it('sends a feed selection to the map target', () => {
    renderDashboard();

    fireEvent.click(screen.getByRole('button', { name: /Luzon earthquake/i }));

    expect(screen.getByText('Map target: e1')).toBeTruthy();
    expect(screen.getByText('Coordinates')).toBeTruthy();
  });

  it('clears the map target and details when the selected event disappears', () => {
    const dashboard = renderDashboard();
    act(() => state.selectOnMap?.(event));
    expect(screen.getByText('Map target: e1')).toBeTruthy();

    state.events = [];
    dashboard.rerender(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );

    expect(screen.getByText('No map target')).toBeTruthy();
    expect(screen.queryByText('Coordinates')).toBeNull();
  });
});
