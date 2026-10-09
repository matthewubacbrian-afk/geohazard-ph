import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import About from '../src/pages/About';
import DataSources from '../src/pages/DataSources';
import HistoricalBrowser from '../src/pages/HistoricalBrowser';

describe('informational pages', () => {
  it('explains the project and the limits of risk profiles', () => {
    render(<About />);

    expect(screen.getByRole('heading', { name: 'About GeoHazard' })).toBeTruthy();
    expect(screen.getByText(/Risk profiles are descriptive statistics, not earthquake predictions\./)).toBeTruthy();
    expect(screen.getByText('GeoHazard PH is not an official PHIVOLCS/NDRRMC advisory.')).toBeTruthy();
  });

  it('describes the methodology without presenting invented risk measurements', async () => {
    const { default: Hero } = await import('../src/pages/Hero');
    render(<Hero />);

    expect(screen.getByRole('heading', { name: /Public hazard data for informed local planning/i })).toBeTruthy();
    expect(screen.queryByText(/predictions\.protection|before the ground shakes/i)).toBeNull();
    expect(screen.queryByText(/sample risk profiling output/i)).toBeNull();
    expect(screen.queryByRole('link', { name: /privacy policy|contact support/i })).toBeNull();
    expect(document.querySelector('a[href="mailto:support@geohazard.ph"]')).toBeNull();
    expect(screen.queryByRole('link', { name: 'Contact' })).toBeNull();
    expect(screen.getAllByText('Risk profiles are descriptive statistics, not earthquake predictions.')).toHaveLength(1);
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
