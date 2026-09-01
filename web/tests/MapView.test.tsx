import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

import MapView from '../src/components/map/MapView';
import { BASEMAPS } from '../src/components/map/basemaps';
import type { HazardEvent } from '../src/types/hazard';

const mapInstance = {
  addControl: vi.fn(),
  addLayer: vi.fn(),
  addSource: vi.fn(),
  getLayer: vi.fn((_id: string) => undefined as { id: string } | undefined),
  on: vi.fn((_event: string, callback: () => void) => callback()),
  remove: vi.fn(),
  setLayoutProperty: vi.fn(),
  setStyle: vi.fn(),
};

vi.mock('maplibre-gl', () => ({
  default: {
    Map: vi.fn(() => mapInstance),
    NavigationControl: vi.fn(),
  },
}));

const fixtureEvents: HazardEvent[] = [
  {
    id: 'e1',
    hazard_type: 'earthquake',
    source: 'usgs',
    magnitude: 4.5,
    depth_km: 10,
    latitude: 14.6,
    longitude: 120.97,
    place_name: 'Luzon',
    occurred_at: '2026-08-29T00:00:00Z',
  },
];

describe('MapView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mapInstance.getLayer.mockReturnValue(undefined);
  });

  it('shows an empty state when there are no events', () => {
    render(<MapView events={[]} />);

    expect(screen.getByText(/no events/i)).toBeTruthy();
  });

  it('adds event marker layers even when the label_country layer is missing', () => {
    render(<MapView events={fixtureEvents} />);

    expect(mapInstance.addSource).toHaveBeenCalledWith(
      'events',
      expect.objectContaining({ type: 'geojson' }),
    );
    expect(mapInstance.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'event-circles' }),
    );
    expect(mapInstance.setLayoutProperty).not.toHaveBeenCalled();
  });

  it('applies the country-label override when the label_country layer exists', () => {
    mapInstance.getLayer.mockReturnValue({ id: 'label_country' });

    render(<MapView events={fixtureEvents} />);

    expect(mapInstance.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'event-circles' }),
    );
    expect(mapInstance.setLayoutProperty).toHaveBeenCalledWith(
      'label_country',
      'text-field',
      expect.any(Array),
    );
  });

  it('does not call setStyle on initial mount', () => {
    render(<MapView events={fixtureEvents} />);

    expect(mapInstance.setStyle).not.toHaveBeenCalled();
  });

  it('calls setStyle with the new style when the basemap changes', () => {
    const { rerender } = render(<MapView events={fixtureEvents} basemap="streets" />);
    rerender(<MapView events={fixtureEvents} basemap="satellite" />);

    expect(mapInstance.setStyle).toHaveBeenCalledWith(BASEMAPS.satellite.style);
  });
});