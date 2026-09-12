import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen } from '@testing-library/react';
import MapView from '../src/components/map/MapView';
import { BASEMAPS, BASEMAP_IDS } from '../src/components/map/basemaps';
import type { StaticLayer } from '../src/types/staticLayer';
import type { HazardEvent } from '../src/types/hazard';
import type { RiskProfile } from '../src/types/hazard';

const handlers = new Map<string, Set<() => void>>();
let source: { setData: ReturnType<typeof vi.fn> } | undefined;
const sources = new Map<string, { setData: ReturnType<typeof vi.fn> }>();
const layers = new Set<string>();
function emit(name: string) { handlers.get(name)?.forEach((callback) => callback()); }
const mapInstance = {
  addControl: vi.fn(),
  addLayer: vi.fn((layer: { id: string }) => layers.add(layer.id)),
  addSource: vi.fn((id: string) => {
    const created = { setData: vi.fn() }; sources.set(id, created);
    if (id === 'events') source = created;
  }),
  getLayer: vi.fn((id: string) => layers.has(id) ? { id } : undefined),
  getSource: vi.fn((id: string) => sources.get(id)),
  getZoom: vi.fn(() => 5),
  getCenter: vi.fn(() => ({ toArray: () => [121.774, 12.8797] })),
  getBearing: vi.fn(() => 0), getPitch: vi.fn(() => 0),
  flyTo: vi.fn(),
  on: vi.fn((name: string, callback: () => void) => {
    if (!handlers.has(name)) handlers.set(name, new Set());
    handlers.get(name)!.add(callback);
  }),
  off: vi.fn((name: string, callback: () => void) => handlers.get(name)?.delete(callback)),
  once: vi.fn(),
  remove: vi.fn(),
  removeLayer: vi.fn((id: string) => layers.delete(id)),
  removeSource: vi.fn((id: string) => { sources.delete(id); if (id === 'events') source = undefined; }),
  setLayoutProperty: vi.fn(),
  setStyle: vi.fn((_style: unknown, _options?: { diff?: boolean }) => {
    source = undefined; layers.clear(); sources.clear();
  }),
};
vi.mock('maplibre-gl', () => ({
  default: { Map: vi.fn(() => mapInstance), NavigationControl: vi.fn() },
}));
const event: HazardEvent = {
  id: 'e1', hazard_type: 'earthquake', source: 'usgs', magnitude: 4.5,
  depth_km: 10, latitude: 14.6, longitude: 120.97, place_name: 'Luzon',
  occurred_at: '2026-08-29T00:00:00Z',
};
const riskProfile: RiskProfile = {
  region_name: 'Bicol Region',
  cluster: 2,
  label: 'High',
  confidence: 0.82,
  feature_importances: {},
  model_version: 'v1',
  generated_at: '2026-08-29T00:00:00Z',
  dataset_snapshot: 'fixture',
};
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
beforeEach(() => {
  vi.clearAllMocks();
  handlers.clear(); layers.clear(); sources.clear(); source = undefined;
  mapInstance.getZoom.mockReturnValue(5);
  vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false })));
});
describe('MapView style lifecycle', () => {
  it('shows an empty state', () => {
    render(<MapView events={[]} />);
    expect(screen.getByText(/no events/i)).toBeTruthy();
  });
  it('renders risk regions and toggles their visibility', () => {
    const view = render(
      <MapView events={[event]} riskProfiles={[riskProfile]} showRiskLayer />,
    );
    act(() => emit('style.load'));

    expect(sources.has('risk-regions')).toBe(true);
    expect(layers.has('risk-regions-fill')).toBe(true);
    expect(mapInstance.setLayoutProperty).toHaveBeenCalledWith(
      'risk-regions-fill',
      'visibility',
      'visible',
    );

    view.rerender(<MapView events={[event]} riskProfiles={[riskProfile]} showRiskLayer={false} />);
    expect(mapInstance.setLayoutProperty).toHaveBeenLastCalledWith(
      'risk-regions-outline',
      'visibility',
      'none',
    );
  });
  it.each(BASEMAP_IDS)('renders markers after the initial %s style loads', (basemap) => {
    render(<MapView events={[event]} basemap={basemap} />);
    expect(mapInstance.addLayer).not.toHaveBeenCalled();
    act(() => emit('style.load'));
    expect(layers.has('event-circles')).toBe(true);
  });
  it.each(BASEMAP_IDS)('restores current events when switching to %s', (basemap) => {
    const initial = basemap === 'streets' ? 'terrain' : 'streets';
    const view = render(<MapView events={[event]} basemap={initial} />);
    act(() => emit('style.load'));
    view.rerender(<MapView events={[event]} basemap={basemap} />);
    expect(mapInstance.setStyle).toHaveBeenCalledWith(BASEMAPS[basemap].style, { diff: false });
    view.rerender(<MapView events={[{ ...event, magnitude: 6 }]} basemap={basemap} />);
    act(() => emit('style.load'));
    expect(layers.has('event-circles')).toBe(true);
    expect(mapInstance.addSource).toHaveBeenLastCalledWith('events', expect.objectContaining({
      data: expect.objectContaining({
        features: [expect.objectContaining({ properties: expect.objectContaining({ magnitude: 6 }) })],
      }),
    }));
    expect(mapInstance.flyTo).not.toHaveBeenCalled();
  });
  it('updates events without replacing the style or camera', () => {
    const view = render(<MapView events={[event]} />);
    act(() => emit('style.load'));
    view.rerender(<MapView events={[{ ...event, magnitude: 7 }]} />);
    expect(source?.setData).toHaveBeenCalled();
    expect(mapInstance.setStyle).not.toHaveBeenCalled();
    expect(mapInstance.flyTo).not.toHaveBeenCalled();
  });
  it('focuses the selected earthquake, including repeat selections', () => {
    const view = render(<MapView events={[event]} selectedEvent={null} />);
    view.rerender(<MapView events={[event]} selectedEvent={event} />);
    expect(mapInstance.flyTo).toHaveBeenLastCalledWith(expect.objectContaining({
      center: [120.97, 14.6], zoom: 8, duration: 800,
    }));
    view.rerender(<MapView events={[event]} selectedEvent={{ ...event }} />);
    expect(mapInstance.flyTo).toHaveBeenCalledTimes(2);
  });
  it('honors reduced motion when focusing', () => {
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true })));
    render(<MapView events={[event]} selectedEvent={event} />);
    expect(mapInstance.flyTo).toHaveBeenCalledWith(expect.objectContaining({ duration: 0 }));
  });
});

const fault: StaticLayer = {
  id: 'fault', external_id: '1', name: 'Test', source: 'gem', source_url: 'https://example.org',
  license_name: 'CC-BY-SA-4.0', dataset_version: 'v1', imported_at: '2026-09-10T00:00:00Z',
  source_properties: {}, geometry: { type: 'LineString', coordinates: [[121, 14], [122, 15]] },
};
describe('static map layers', () => {
  it('restores current geometry and toggles after a basemap switch', () => {
    const view = render(<MapView events={[event]} faults={[fault]} showFaults />);
    act(() => emit('style.load'));
    expect(layers.has('faults')).toBe(true);
    expect(sources.has('volcano-zones')).toBe(true);
    expect(mapInstance.setLayoutProperty).toHaveBeenCalledWith('faults', 'visibility', 'visible');
    view.rerender(<MapView events={[]} faults={[fault]} showFaults={false} showEvents={false} basemap="terrain" />);
    act(() => emit('style.load'));
    expect(mapInstance.setLayoutProperty).toHaveBeenCalledWith('faults', 'visibility', 'none');
    expect(mapInstance.setLayoutProperty).toHaveBeenLastCalledWith('event-circles', 'visibility', 'none');
    expect(mapInstance.addSource).toHaveBeenCalledWith('faults', expect.objectContaining({
      data: expect.objectContaining({features: [expect.objectContaining({geometry: fault.geometry})]}),
    }));
  });
  it('updates reference geometry without moving the camera', () => {
    const view = render(<MapView events={[]} />);
    act(() => emit('style.load'));
    view.rerender(<MapView events={[]} faults={[fault]} showFaults />);
    expect(sources.get('faults')?.setData).toHaveBeenCalledWith(expect.objectContaining({
      features: [expect.objectContaining({geometry: fault.geometry})],
    }));
    expect(mapInstance.flyTo).not.toHaveBeenCalled();
  });
});
