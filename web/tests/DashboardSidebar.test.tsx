import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';

import DashboardSidebar from '../src/components/dashboard/DashboardSidebar';
import type { BasemapId } from '../src/components/map/basemaps';

afterEach(cleanup);

function renderSidebar(
  overrides: {
    basemap?: BasemapId;
    onBasemapChange?: () => void;
    onToggleLayer?: (key: string) => void;
    onDatePresetChange?: (preset: '1d' | '7d' | '30d' | '90d') => void;
    onMinMagnitudeChange?: (value: number) => void;
    onToggleHazardType?: (type: 'earthquake' | 'volcanic' | 'landslide') => void;
    onSourceChange?: (source: string) => void;
    source?: string;
    collapsed?: boolean;
    onToggleCollapsed?: () => void;
    onViewChange?: (view: 'map' | 'filters' | 'history' | 'risk' | 'volcanoes') => void;
  } = {},
) {
  return render(
    <DashboardSidebar
      basemap={overrides.basemap ?? 'streets'}
      onBasemapChange={overrides.onBasemapChange ?? vi.fn()}
      activeView="map"
      onViewChange={overrides.onViewChange ?? vi.fn()}
      collapsed={overrides.collapsed ?? false}
      onToggleCollapsed={overrides.onToggleCollapsed ?? vi.fn()}
      activeLayers={{ events: true, risk: false }}
      onToggleLayer={overrides.onToggleLayer ?? vi.fn()}
      activeEventCategories={['critical', 'elevated', 'baseline']}
      onToggleEventCategory={vi.fn()}
      startDate=""
      endDate=""
      onStartDateChange={vi.fn()}
      onEndDateChange={vi.fn()}
      minMagnitude={1}
      onMinMagnitudeChange={overrides.onMinMagnitudeChange ?? vi.fn()}
      activeHazardTypes={['earthquake', 'volcanic', 'landslide']}
      onToggleHazardType={overrides.onToggleHazardType ?? vi.fn()}
      onDatePresetChange={overrides.onDatePresetChange ?? vi.fn()}
      source={overrides.source ?? ''}
      onSourceChange={overrides.onSourceChange ?? vi.fn()}
    />,
  );
}

describe('DashboardSidebar map layers', () => {
  it('shows the current basemap on the trigger button', () => {
    renderSidebar({ basemap: 'satellite' });

    expect(screen.getByRole('button', { name: 'Satellite' })).toHaveAttribute('aria-pressed', 'true');
  });

  it('offers an independent landslide susceptibility toggle', () => {
    const onToggleLayer = vi.fn();
    renderSidebar({ onToggleLayer });

    fireEvent.click(screen.getByLabelText('Landslide susceptibility'));

    expect(onToggleLayer).toHaveBeenCalledWith('landslideSusceptibility');
  });

  it('shows all four existing basemap options as connected controls', () => {
    renderSidebar();

    for (const label of ['Streets', 'Satellite', 'Hybrid', 'Terrain']) {
      expect(screen.getByRole('button', { name: label })).toBeInTheDocument();
    }
  });

  it('calls onBasemapChange with the chosen basemap', () => {
    const onBasemapChange = vi.fn();
    renderSidebar({ basemap: 'streets', onBasemapChange });

    fireEvent.click(screen.getByRole('button', { name: 'Hybrid' }));

    expect(onBasemapChange).toHaveBeenCalledWith('hybrid');
  });
});

describe('DashboardSidebar layers', () => {
  it('collapses to a named icon rail and opens a chosen dashboard view', () => {
    const onViewChange = vi.fn();
    const onToggleCollapsed = vi.fn();
    renderSidebar({ collapsed: true, onViewChange, onToggleCollapsed });

    fireEvent.click(screen.getByRole('button', { name: 'Open Risk reports' }));

    expect(onViewChange).toHaveBeenCalledWith('risk');
    expect(onToggleCollapsed).toHaveBeenCalledTimes(1);
    expect(screen.queryByLabelText('Minimum magnitude')).not.toBeInTheDocument();
  });
  it('keeps accessible names for every view, toggle, date, basemap, and magnitude control', () => {
    renderSidebar();

    for (const label of ['Map', 'Seismic filters', 'Historical data', 'Volcano bulletins', 'Risk reports']) {
      expect(screen.getByRole('button', { name: new RegExp(`^${label}$`) })).toBeInTheDocument();
    }
    for (const label of ['Live events', 'Risk overlay', 'Fault lines', 'Volcano zones', 'Landslide susceptibility']) {
      expect(screen.getByLabelText(label)).toBeInTheDocument();
    }
    for (const label of ['Critical events', 'Elevated events', 'Baseline events']) {
      expect(screen.getByLabelText(label)).toBeInTheDocument();
    }
    expect(screen.getByRole('group', { name: 'Map layers' })).toBeInTheDocument();
    expect(screen.getByRole('group', { name: 'Event source' })).toBeInTheDocument();
    expect(screen.getByLabelText('Earthquake')).toBeInTheDocument();
    expect(screen.getByLabelText('Start date')).toBeInTheDocument();
    expect(screen.getByLabelText('End date')).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Minimum magnitude' })).toBeInTheDocument();
  });

  it('labels event buckets separately from regional risk profiles', () => {
    renderSidebar();

    expect(screen.getByRole('heading', { name: 'Risk category' })).toBeInTheDocument();
    for (const label of ['Critical events', 'Elevated events', 'Baseline events']) {
      expect(screen.getByLabelText(label)).toBeInTheDocument();
    }
  });
  it('calls onToggleLayer when a layer checkbox is toggled', () => {
    const onToggleLayer = vi.fn();
    renderSidebar({ onToggleLayer });

    fireEvent.click(screen.getByLabelText(/live events/i));

    expect(onToggleLayer).toHaveBeenCalledWith('events');
  });

  it('enables imported reference layer controls', () => {
    renderSidebar();

    const faults = screen.getByLabelText(/fault lines/i) as HTMLInputElement;
    expect(faults.disabled).toBe(false);
  });

  it('connects date window presets, magnitude thresholds and hazard type controls', () => {
    const onDatePresetChange = vi.fn();
    const onMinMagnitudeChange = vi.fn();
    const onToggleHazardType = vi.fn();
    renderSidebar({ onDatePresetChange, onMinMagnitudeChange, onToggleHazardType });

    fireEvent.click(screen.getByRole('button', { name: '30D' }));
    fireEvent.click(screen.getByRole('button', { name: '≥ 2.5' }));
    fireEvent.click(screen.getByLabelText('Volcano activity'));

    expect(onDatePresetChange).toHaveBeenCalledWith('30d');
    expect(onMinMagnitudeChange).toHaveBeenCalledWith(2.5);
    expect(onToggleHazardType).toHaveBeenCalledWith('volcanic');
  });
});
