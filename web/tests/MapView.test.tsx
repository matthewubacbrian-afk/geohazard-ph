import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { act } from 'react';

import MapView from '../src/components/map/MapView';

const mapInstance = {
  addControl: vi.fn(),
  addLayer: vi.fn(),
  addSource: vi.fn(),
  remove: vi.fn(),
  setLayoutProperty: vi.fn(),
  on: vi.fn((_event: string, callback: () => void) => callback()),
};

vi.mock('maplibre-gl', () => ({
  default: {
    Map: vi.fn(() => mapInstance),
    NavigationControl: vi.fn(),
  },
}));

describe('MapView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows an empty state when there are no events', () => {
    render(<MapView events={[]} />);

    expect(screen.getByText(/no events/i)).toBeTruthy();
  });
});
