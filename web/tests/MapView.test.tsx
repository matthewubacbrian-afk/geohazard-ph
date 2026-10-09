import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen } from '@testing-library/react';
import MapView from '../src/components/map/MapView';
import { BASEMAPS, BASEMAP_IDS } from '../src/components/map/basemaps';
import type { StaticLayer } from '../src/types/staticLayer';
import type { HazardEvent } from '../src/types/hazard';
import type { RiskProfile } from '../src/types/hazard';

const handlers = new Map<string, Set<() => void>>();
const layerHandlers = new Map<string, (event: { features?: Array<{ properties?: Record<string, unknown> }> }) => void>();
const paintUpdates: Array<[string, string, unknown]> = [];
let source: { setData: ReturnType<typeof vi.fn> } | undefined;
const sources = new Map<string, { setData: ReturnType<typeof vi.fn> }>();
const layers = new Set<string>();
function emit(name: string) { handlers.get(name)?.forEach((callback) => callback()); }
const mapInstance = {
  addControl: vi.fn(),
  addLayer: vi.fn((layer: { id: string; paint?: Record<string, unknown> }) => layers.add(layer.id)),
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
  on: vi.fn((name: string, layerOrCallback: string | (() => void), maybeCallback?: (event: { features?: Array<{ properties?: Record<string, unknown> }> }) => void) => {
    if (typeof layerOrCallback === 'string' && maybeCallback) { layerHandlers.set(layerOrCallback, maybeCallback); return; }
    const callback = layerOrCallback as () => void;
    if (!handlers.has(name)) handlers.set(name, new Set());
    handlers.get(name)!.add(callback);
  }),
  off: vi.fn((name: string, layerOrCallback: string | (() => void), maybeCallback?: () => void) => {
    if (typeof layerOrCallback === 'string') { layerHandlers.delete(layerOrCallback); return; }
    handlers.get(name)?.delete(layerOrCallback);
  }),
  once: vi.fn(),
  remove: vi.fn(),
  removeLayer: vi.fn((id: string) => layers.delete(id)),
  removeSource: vi.fn((id: string) => { sources.delete(id); if (id === 'events') source = undefined; }),
  setLayoutProperty: vi.fn(),
  setPaintProperty: vi.fn((layer: string, property: string, value: unknown) => paintUpdates.push([layer, property, value])),
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
  layerHandlers.clear(); paintUpdates.length = 0;
  mapInstance.getZoom.mockReturnValue(5);
  vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false })));
});
describe('MapView style lifecycle', () => {
  it('selects the event represented by a clicked map circle', () => {
    const onSelectEvent = vi.fn();
    render(<MapView events={[event]} onSelectEvent={onSelectEvent} />);
    act(() => emit('style.load'));
    act(() => layerHandlers.get('event-circles')?.({ features: [{ properties: { eventId: 'e1' } }] }));
    expect(onSelectEvent).toHaveBeenCalledWith(event);
  });
  it('ignores clicked circles with a missing or unknown event ID', () => {
    const onSelectEvent = vi.fn();
    const view = render(<MapView events={[event]} onSelectEvent={onSelectEvent} />);
    act(() => emit('style.load'));
    act(() => layerHandlers.get('event-circles')?.({ features: [{ properties: {} }] }));
    view.rerender(<MapView events={[]} onSelectEvent={onSelectEvent} />);
    act(() => layerHandlers.get('event-circles')?.({ features: [{ properties: { eventId: 'e1' } }] }));
    expect(onSelectEvent).not.toHaveBeenCalled();
  });
  it('replaces the click handler after a style reload and removes it on unmount', () => {
    const view = render(<MapView events={[event]} onSelectEvent={vi.fn()} />);
    act(() => emit('style.load'));
    const firstHandler = layerHandlers.get('event-circles');
    expect(firstHandler).toBeDefined();

    act(() => emit('style.load'));
    const restoredHandler = layerHandlers.get('event-circles');
    expect(restoredHandler).toBeDefined();
    expect(restoredHandler).not.toBe(firstHandler);
    expect(mapInstance.off).toHaveBeenCalledWith('click', 'event-circles', firstHandler);

    view.unmount();
    expect(layerHandlers.has('event-circles')).toBe(false);
    expect(mapInstance.off).toHaveBeenCalledWith('click', 'event-circles', restoredHandler);
  });
  it('keeps one selected point in the halo source and clears it on deselection', () => {
    const cancel = vi.fn();
    vi.stubGlobal('requestAnimationFrame', vi.fn(() => 7));
    vi.stubGlobal('cancelAnimationFrame', cancel);
    const selected = { ...event, id: 'e2', longitude: 122, latitude: 15 };
    const view = render(<MapView events={[event, selected]} selectedEvent={event} />);
    act(() => emit('style.load'));
    expect(mapInstance.addSource).toHaveBeenCalledWith('selected-event', expect.objectContaining({ data: expect.objectContaining({ features: [expect.objectContaining({ geometry: { type: 'Point', coordinates: [120.97, 14.6] } })] }) }));
    view.rerender(<MapView events={[event, selected]} selectedEvent={selected} />);
    expect(sources.get('selected-event')?.setData).toHaveBeenLastCalledWith(expect.objectContaining({ features: [expect.objectContaining({ geometry: { type: 'Point', coordinates: [122, 15] } })] }));
    view.rerender(<MapView events={[event, selected]} selectedEvent={null} />);
    expect(sources.get('selected-event')?.setData).toHaveBeenLastCalledWith(expect.objectContaining({ features: [] }));
    expect(cancel).toHaveBeenCalledWith(7);
  });
  it('uses a static halo without scheduling frames when reduced motion is preferred', () => {
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true })));
    const request = vi.fn();
    vi.stubGlobal('requestAnimationFrame', request);
    render(<MapView events={[event]} selectedEvent={event} />);
    act(() => emit('style.load'));
    const halo = mapInstance.addLayer.mock.calls.find(([layer]) => layer.id === 'selected-event-pulse')?.[0];
    expect(halo?.paint?.['circle-opacity']).toBeGreaterThan(0);
    expect(request).not.toHaveBeenCalled();
  });
  it('animates only the selected halo in normal motion', () => {
    const colors = {
      '--magnitude-low': '#4d6038',
      '--magnitude-moderate': '#645024',
      '--magnitude-high': '#873d2d',
      '--magnitude-very-high': '#6d2c24',
    };
    for (const [name, value] of Object.entries(colors)) document.documentElement.style.setProperty(name, value);
    const request = vi.fn(() => 1);
    vi.stubGlobal('requestAnimationFrame', request);
    render(<MapView events={[event]} selectedEvent={event} />);
    act(() => emit('style.load'));
    expect(request).toHaveBeenCalledTimes(1);
    expect(paintUpdates.every(([layer]) => layer === 'selected-event-pulse')).toBe(true);
    expect(mapInstance.addLayer.mock.calls.find(([layer]) => layer.id === 'event-circles')?.[0].paint?.['circle-radius']).toEqual([
      'interpolate', ['linear'], ['max', 0, ['min', 9, ['coalesce', ['get', 'magnitude'], 0]]], 0, 4, 9, 13,
    ]);
    expect(mapInstance.addLayer.mock.calls.find(([layer]) => layer.id === 'event-circles')?.[0].paint?.['circle-color']).toEqual([
      'step', ['coalesce', ['get', 'magnitude'], 0], colors['--magnitude-low'], 3,
      colors['--magnitude-moderate'], 5, colors['--magnitude-high'], 7, colors['--magnitude-very-high'],
    ]);
    for (const name of Object.keys(colors)) document.documentElement.style.removeProperty(name);
  });
  it('keeps one scheduled animation loop when the selected event changes', () => {
    const pendingFrames = new Map<number, FrameRequestCallback>();
    let nextFrameId = 1;
    const request = vi.fn((callback: FrameRequestCallback) => {
      const id = nextFrameId++;
      pendingFrames.set(id, callback);
      return id;
    });
    const cancel = vi.fn((id: number) => { pendingFrames.delete(id); });
    vi.stubGlobal('requestAnimationFrame', request);
    vi.stubGlobal('cancelAnimationFrame', cancel);
    const secondEvent = { ...event, id: 'e2', longitude: 122, latitude: 15 };
    const view = render(<MapView events={[event, secondEvent]} selectedEvent={event} />);
    act(() => emit('style.load'));
    expect(pendingFrames.size).toBe(1);

    view.rerender(<MapView events={[event, secondEvent]} selectedEvent={secondEvent} />);
    expect(pendingFrames.size).toBe(1);
    expect(request).toHaveBeenCalledTimes(1);
  });
  it('cancels the pending animation frame on unmount', () => {
    const pendingFrames = new Map<number, FrameRequestCallback>();
    const request = vi.fn((callback: FrameRequestCallback) => {
      pendingFrames.set(23, callback);
      return 23;
    });
    const cancel = vi.fn((id: number) => { pendingFrames.delete(id); });
    vi.stubGlobal('requestAnimationFrame', request);
    vi.stubGlobal('cancelAnimationFrame', cancel);
    const view = render(<MapView events={[event]} selectedEvent={event} />);
    expect(pendingFrames.has(23)).toBe(true);

    view.unmount();

    expect(cancel).toHaveBeenCalledWith(23);
    expect(pendingFrames.has(23)).toBe(false);
  });
  it('updates only halo paint per frame and skips updates when its layer is absent', () => {
    const pendingFrames = new Map<number, FrameRequestCallback>();
    let nextFrameId = 1;
    const request = vi.fn((callback: FrameRequestCallback) => {
      const id = nextFrameId++;
      pendingFrames.set(id, callback);
      return id;
    });
    vi.stubGlobal('requestAnimationFrame', request);
    render(<MapView events={[event]} selectedEvent={event} />);
    act(() => emit('style.load'));
    const first = pendingFrames.entries().next().value as [number, FrameRequestCallback];
    pendingFrames.delete(first[0]);
    act(() => first[1](0));
    expect(paintUpdates).toEqual([
      ['selected-event-pulse', 'circle-radius', 13],
      ['selected-event-pulse', 'circle-opacity', 0.52],
    ]);

    paintUpdates.length = 0;
    layers.delete('selected-event-pulse');
    const next = pendingFrames.entries().next().value as [number, FrameRequestCallback];
    pendingFrames.delete(next[0]);
    act(() => next[1](900));
    expect(paintUpdates).toEqual([]);
    expect(pendingFrames.size).toBe(1);
  });
  it('shows an empty state', () => {
    render(<MapView events={[]} />);
    expect(screen.getByText(/no events/i)).toBeTruthy();
  });
  it('bounds event marker size by the existing magnitude range', () => {
    render(<MapView events={[event]} />);
    act(() => emit('style.load'));

    const eventLayer = mapInstance.addLayer.mock.calls.find(([layer]) => layer.id === 'event-circles');
    expect(eventLayer?.[0].paint?.['circle-radius']).toEqual([
      'interpolate', ['linear'],
      ['max', 0, ['min', 9, ['coalesce', ['get', 'magnitude'], 0]]],
      0, 4,
      9, 13,
    ]);
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
    expect(mapInstance.setLayoutProperty).toHaveBeenCalledWith('risk-regions-outline', 'visibility', 'none');
    expect(mapInstance.setLayoutProperty).toHaveBeenCalledWith('risk-regions-outline-high', 'visibility', 'none');
  });
  it('assigns distinct overlay colors to each canonical risk label', () => {
    const colors = {
      '--risk-very-high': '#702820',
      '--risk-high': '#99422f',
      '--risk-moderate': '#75500e',
      '--risk-low': '#315b4c',
      '--surface-card': '#fffefa',
    };
    for (const [name, value] of Object.entries(colors)) {
      document.documentElement.style.setProperty(name, value);
    }
    render(<MapView events={[]} riskProfiles={[riskProfile]} showRiskLayer />);
    act(() => emit('style.load'));

    const riskLayer = mapInstance.addLayer.mock.calls.find(([layer]) => layer.id === 'risk-regions-fill');
    expect(riskLayer?.[0].paint?.['fill-color']).toEqual([
      'match', ['get', 'label'],
      'Very High', colors['--risk-very-high'],
      'High', colors['--risk-high'],
      'Moderate', colors['--risk-moderate'],
      'Low', colors['--risk-low'],
      expect.any(String),
    ]);
    const patternedOutline = mapInstance.addLayer.mock.calls.find(([layer]) => layer.id === 'risk-regions-outline-high');
    expect(patternedOutline?.[0]).toMatchObject({ filter: ['==', ['get', 'label'], 'High'], paint: { 'line-dasharray': [1, 1] } });
    const haloOutline = mapInstance.addLayer.mock.calls.find(([layer]) => layer.id === 'risk-regions-outline');
    expect(haloOutline?.[0].paint).toMatchObject({ 'line-color': '#fffefa', 'line-width': 3 });
    for (const name of Object.keys(colors)) document.documentElement.style.removeProperty(name);
  });
  it('shows a distinct boundary pattern for every risk label and hides all cues when disabled', () => {
    const cues = [
      { label: 'Low', id: 'risk-regions-outline-low', dash: [1, 0] },
      { label: 'Moderate', id: 'risk-regions-outline-moderate', dash: [2, 1] },
      { label: 'High', id: 'risk-regions-outline-high', dash: [1, 1] },
      { label: 'Very High', id: 'risk-regions-outline-very-high', dash: [3, 1, 1, 1] },
    ];
    const view = render(<MapView events={[]} riskProfiles={[riskProfile]} showRiskLayer />);
    act(() => emit('style.load'));

    for (const cue of cues) {
      const layer = mapInstance.addLayer.mock.calls.find(([candidate]) => candidate.id === cue.id);
      expect(layer?.[0]).toMatchObject({
        filter: ['==', ['get', 'label'], cue.label],
        paint: { 'line-dasharray': cue.dash },
      });
      expect(mapInstance.setLayoutProperty).toHaveBeenCalledWith(cue.id, 'visibility', 'visible');
    }

    view.rerender(<MapView events={[]} riskProfiles={[riskProfile]} showRiskLayer={false} />);
    for (const cue of cues) {
      expect(mapInstance.setLayoutProperty).toHaveBeenCalledWith(cue.id, 'visibility', 'none');
    }
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
    const restoredEventsSource = [...mapInstance.addSource.mock.calls].reverse().find(([id]) => id === 'events');
    expect(restoredEventsSource?.[1]).toEqual(expect.objectContaining({
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

describe('map symbol palette', () => {
  it('renders magnitude ranges with size/color cues and an accessible event summary', () => {
    render(<MapView events={[event, { ...event, id: 'e2', magnitude: 7.2 }]} />);

    expect(screen.getByRole('region', { name: 'Hazard event map' })).toHaveAccessibleDescription(
      '2 events shown on the map.',
    );
    const legend = screen.getByRole('region', { name: 'Magnitude legend' });
    expect(legend).toHaveTextContent('Magnitude');
    expect(legend).not.toHaveTextContent(/Mw|Lower|Moderate|High|Very high/i);
    expect(legend).toHaveTextContent('0–2.9');
    expect(legend).toHaveTextContent('3.0–4.9');
    expect(legend).toHaveTextContent('5.0–6.9');
    expect(legend).toHaveTextContent('7.0+');
    expect(legend).toHaveTextContent('small');
    expect(legend).toHaveTextContent('medium');
    expect(legend).toHaveTextContent('large');
    expect(legend).toHaveTextContent('largest');
  });
  it('uses an escalating Warm Field magnitude ramp and a high-contrast marker halo', () => {
    const tokens = { '--magnitude-low': '#4d6038', '--magnitude-moderate': '#645024', '--magnitude-high': '#873d2d', '--magnitude-very-high': '#6d2c24', '--surface-card': '#fffcf5' };
    for (const [name, value] of Object.entries(tokens)) document.documentElement.style.setProperty(name, value);
    render(<MapView events={[event]} />);
    act(() => emit('style.load'));
    const paint = mapInstance.addLayer.mock.calls.find(([layer]) => layer.id === 'event-circles')?.[0].paint;
    expect(paint?.['circle-color']).toEqual([
      'step', ['coalesce', ['get', 'magnitude'], 0], '#4d6038', 3, '#645024', 5, '#873d2d', 7, '#6d2c24',
    ]);
    expect(paint?.['circle-radius']).toEqual([
      'interpolate', ['linear'], ['max', 0, ['min', 9, ['coalesce', ['get', 'magnitude'], 0]]], 0, 4, 9, 13,
    ]);
    expect(paint?.['circle-stroke-width']).toBe(2.5);
    expect(paint?.['circle-stroke-color']).toBe('#fffcf5');
    for (const name of Object.keys(tokens)) document.documentElement.style.removeProperty(name);
  });
});
