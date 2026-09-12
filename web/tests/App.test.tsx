import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../src/components/map/MapView', () => ({
  default: () => <div aria-label="Geospatial risk dashboard map" />,
}));

import App from '../src/App';

describe('application routes', () => {
  it.each([
    ['/', /Patterns\.Predictions\.Protection/i],
    ['/about', /About GeoHazard/i],
    ['/data-sources', /Data Sources/i],
    ['/historical', /Historical Event Browser/i],
  ])('renders the page at %s', (path, heading) => {
    window.history.pushState({}, '', path);
    render(<App />);

    expect(screen.getByRole('heading', { name: heading })).toBeTruthy();
  });

  it('redirects unknown paths to the hero page', () => {
    window.history.pushState({}, '', '/missing');
    render(<App />);

    expect(screen.getByText(/Patterns\.Predictions\.Protection/i)).toBeTruthy();
  });

  it('navigates through the shared navigation without local view state', () => {
    window.history.pushState({}, '', '/');
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: 'About' }));

    expect(screen.getByRole('heading', { name: 'About GeoHazard' })).toBeTruthy();
    expect(window.location.pathname).toBe('/about');
  });
});