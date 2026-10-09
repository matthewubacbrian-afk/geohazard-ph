import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../src/components/map/MapView', () => ({
  default: () => <div aria-label="Geospatial risk dashboard map" />,
}));

import App from '../src/App';

describe('application routes', () => {
  it.each([
    ['/', /Public hazard data for informed local planning/i],
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

    expect(screen.getByRole('heading', { name: /Public hazard data for informed local planning/i })).toBeTruthy();
  });

  it('navigates through the shared navigation without local view state', () => {
    window.history.pushState({}, '', '/');
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: 'About' }));

    expect(screen.getByRole('heading', { name: 'About GeoHazard' })).toBeTruthy();
    expect(window.location.pathname).toBe('/about');
  });

  it('keeps shared navigation controls keyboard reachable and identifies the current page', () => {
    window.history.pushState({}, '', '/about');
    render(<App />);

    expect(screen.getByRole('navigation', { name: 'Main navigation' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'About' })).toHaveAttribute('aria-current', 'page');
    const dataSources = screen.getByRole('button', { name: 'Data Sources' });
    dataSources.focus();
    expect(dataSources).toHaveFocus();
    const settings = screen.getByRole('button', { name: 'Settings' });
    settings.focus();
    expect(settings).toHaveFocus();
  });
});
