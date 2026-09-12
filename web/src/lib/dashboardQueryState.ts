import type { BasemapId } from '../components/map/basemaps';
import type { DashboardView } from '../components/dashboard/DashboardSidebar';

export type DashboardQueryState = {
  view: DashboardView;
  source: string;
  startDate: string;
  endDate: string;
  minMagnitude: number;
  basemap: BasemapId;
};

export const DEFAULT_DASHBOARD_QUERY: DashboardQueryState = {
  view: 'map',
  source: '',
  startDate: '',
  endDate: '',
  minMagnitude: 1,
  basemap: 'streets',
};

const DASHBOARD_VIEWS: DashboardView[] = ['map', 'filters', 'history', 'risk', 'volcanoes'];
const BASEMAPS: BasemapId[] = ['streets', 'satellite', 'hybrid', 'terrain'];
const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

function valueIn<T extends string>(value: string | null, allowed: T[]): T | null {
  return value && allowed.includes(value as T) ? (value as T) : null;
}

function validDate(value: string | null): string {
  return value && DATE_PATTERN.test(value) ? value : '';
}

function validMagnitude(value: string | null): number {
  if (!value) return DEFAULT_DASHBOARD_QUERY.minMagnitude;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 1 && parsed <= 9 ? parsed : DEFAULT_DASHBOARD_QUERY.minMagnitude;
}

export function parseDashboardQuery(search: string): DashboardQueryState {
  const params = new URLSearchParams(search.startsWith('?') ? search.slice(1) : search);
  return {
    view: valueIn(params.get('view'), DASHBOARD_VIEWS) ?? DEFAULT_DASHBOARD_QUERY.view,
    source: params.get('source')?.trim() ?? DEFAULT_DASHBOARD_QUERY.source,
    startDate: validDate(params.get('start')),
    endDate: validDate(params.get('end')),
    minMagnitude: validMagnitude(params.get('minMagnitude')),
    basemap: valueIn(params.get('basemap'), BASEMAPS) ?? DEFAULT_DASHBOARD_QUERY.basemap,
  };
}

export function serializeDashboardQuery(state: DashboardQueryState): string {
  const params = new URLSearchParams();
  if (state.view !== DEFAULT_DASHBOARD_QUERY.view) params.set('view', state.view);
  if (state.source) params.set('source', state.source);
  if (state.startDate) params.set('start', state.startDate);
  if (state.endDate) params.set('end', state.endDate);
  if (state.minMagnitude !== DEFAULT_DASHBOARD_QUERY.minMagnitude) {
    params.set('minMagnitude', String(state.minMagnitude));
  }
  if (state.basemap !== DEFAULT_DASHBOARD_QUERY.basemap) params.set('basemap', state.basemap);
  return params.toString();
}