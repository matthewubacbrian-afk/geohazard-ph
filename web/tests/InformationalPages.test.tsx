import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import About from '../src/pages/About';
import DataSources from '../src/pages/DataSources';
import HistoricalBrowser from '../src/pages/HistoricalBrowser';

describe('informational pages', () => {
  it('explains the project and the limits of risk profiles', () => {
    render(<About />);

    expect(screen.getByRole('heading', { name: 'About GeoHazard' })).toBeTruthy();
    expect(screen.getByText(/descriptive statistical profiles rather than predictions/i)).toBeTruthy();
  });

  it('identifies current sources and attribution', () => {
    render(<DataSources />);

    expect(screen.getByRole('heading', { name: 'Data Sources' })).toBeTruthy();
    expect(screen.getByText(/USGS Earthquake Catalog/i)).toBeTruthy();
    expect(screen.getAllByText(/PHIVOLCS/i).length).toBeGreaterThan(0);
  });

  it('describes the historical browser as a future feature', () => {
    render(<HistoricalBrowser />);

    expect(screen.getByRole('heading', { name: 'Historical Event Browser' })).toBeTruthy();
    expect(screen.getByText(/future feature/i)).toBeTruthy();
    expect(screen.getByRole('link', { name: /open live dashboard/i })).toHaveAttribute(
      'href',
      '/dashboard',
    );
    expect(screen.queryByRole('textbox')).toBeNull();
  });
});