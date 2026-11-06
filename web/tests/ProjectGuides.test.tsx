import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import Hero from '../src/pages/Hero';
import DataSources from '../src/pages/DataSources';
import HistoricalBrowser from '../src/pages/HistoricalBrowser';

describe('visitor project guides', () => {
  it('explains the active data flow separately from device analysis and research', () => {
    render(<Hero />);
    expect(screen.getByRole('heading', { name: 'From source to screen' })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Scene review on your device' })).toBeVisible();
    expect(screen.getByRole('link', { name: 'Try Scene Review' })).toHaveAttribute('href', '/scene-analysis');
    expect(screen.getByText(/under review and are not published as approved risk guidance/)).toBeVisible();
  });
  it('links directly to source providers and distinguishes map snapshots from event feeds', () => {
    render(<DataSources />);
    expect(screen.getByRole('link', { name: 'View USGS catalog' })).toHaveAttribute('href', 'https://earthquake.usgs.gov/earthquakes/search/');
    expect(screen.getByRole('link', { name: 'PHIVOLCS earthquake bulletins' })).toHaveAttribute('href', 'https://earthquake.phivolcs.dost.gov.ph/');
    expect(screen.getByRole('link', { name: 'View GEM fault dataset' })).toHaveAttribute('href', 'https://github.com/GEMScienceTools/gem-global-active-faults');
    expect(screen.getByText(/pinned 17-region snapshot/)).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Map references' })).toBeVisible();
  });
  it('offers working source-filter links while keeping the dedicated archive clearly planned', () => {
    render(<HistoricalBrowser />);
    expect(screen.getByRole('link', { name: 'Browse PHIVOLCS records' })).toHaveAttribute('href', '/dashboard?view=history&source=phivolcs');
    expect(screen.getByRole('link', { name: 'Browse USGS records' })).toHaveAttribute('href', '/dashboard?view=history&source=usgs');
    expect(screen.getByText(/future feature/)).toBeVisible();
    expect(screen.queryByRole('textbox')).toBeNull();
  });
});
