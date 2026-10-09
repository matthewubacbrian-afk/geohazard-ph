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
  } = {},
) {
  return render(
    <DashboardSidebar
      basemap={overrides.basemap ?? 'streets'}
      onBasemapChange={overrides.onBasemapChange ?? vi.fn()}
      activeView="map"
      onViewChange={vi.fn()}
      activeLayers={{ events: true, risk: false }}
      onToggleLayer={overrides.onToggleLayer ?? vi.fn()}
      activeEventCategories={['critical', 'elevated', 'baseline']}
      onToggleEventCategory={vi.fn()}
      startDate=""
      endDate=""
      onStartDateChange={vi.fn()}
      onEndDateChange={vi.fn()}
      minMagnitude={1}
      onMinMagnitudeChange={vi.fn()}
    />,
  );
}

describe('DashboardSidebar map layers dropdown', () => {
  it('shows the current basemap on the trigger button', () => {
    renderSidebar({ basemap: 'satellite' });

    expect(screen.getByRole('button', { name: /satellite/i })).toBeTruthy();
  });

  it('lists all four basemap options when opened', () => {
    renderSidebar();

    fireEvent.click(screen.getByRole('button', { name: /map layers/i, expanded: false }));

    for (const label of ['Streets', 'Satellite', 'Hybrid', 'Terrain']) {
      expect(screen.getByRole('menuitem', { name: new RegExp(label) })).toBeTruthy();
    }
  });

  it('calls onBasemapChange with the chosen basemap and closes the menu', () => {
    const onBasemapChange = vi.fn();
    renderSidebar({ basemap: 'streets', onBasemapChange });

    fireEvent.click(screen.getByRole('button', { name: /map layers/i }));
    fireEvent.click(screen.getByRole('menuitem', { name: /hybrid/i }));

    expect(onBasemapChange).toHaveBeenCalledWith('hybrid');
    expect(screen.queryByRole('menuitem')).toBeNull();
  });
});

describe('DashboardSidebar layers', () => {
  it('keeps accessible names for every view, toggle, date, basemap, and magnitude control', () => {
    renderSidebar();

    for (const label of ['Map', 'Seismic filters', 'Historical data', 'Volcano bulletins', 'Risk reports']) {
      expect(screen.getByRole('button', { name: new RegExp(`^${label}$`) })).toBeInTheDocument();
    }
    for (const label of ['Live events', 'Risk overlay', 'Fault lines', 'Volcano zones']) {
      expect(screen.getByLabelText(label)).toBeInTheDocument();
    }
    for (const label of ['Critical events', 'Elevated events', 'Baseline events']) {
      expect(screen.getByLabelText(label)).toBeInTheDocument();
    }
    expect(screen.getByRole('button', { name: /map layers/i })).toBeInTheDocument();
    expect(screen.getByLabelText('Start date')).toBeInTheDocument();
    expect(screen.getByLabelText('End date')).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Minimum magnitude' })).toBeInTheDocument();
  });

  it('labels event buckets separately from regional risk profiles', () => {
    renderSidebar();

    expect(screen.getByRole('heading', { name: 'Event feed categories' })).toBeInTheDocument();
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
});
