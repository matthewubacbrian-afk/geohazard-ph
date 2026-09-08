import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, describe, expect, it } from 'vitest';
import { useState } from 'react';

import EventFilterBar from '../src/components/events/EventFilterBar';
import RealtimeStatus from '../src/components/dashboard/RealtimeStatus';
import EventFeed from '../src/components/events/EventFeed';
import { useEvents } from '../src/hooks/useEvents';
import type { HazardEvent } from '../src/types/hazard';

const row: HazardEvent = {
  id: 'one', hazard_type: 'earthquake', source: 'usgs', latitude: 15, longitude: 121,
  place_name: 'USGS event', occurred_at: '2026-08-29T09:30:00Z', magnitude: 5,
};
function Feed() {
  const [source, setSource] = useState('');
  const { data = [] } = useEvents(source);
  return <><EventFilterBar source={source} onChange={setSource} />
    <EventFeed events={data} isLoading={false} error={null} onRetry={() => {}} /></>;
}
afterEach(cleanup);
describe('live event display', () => {
  it('filters shared live data by source for map/list consumers', async () => {
    const client = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity } } });
    client.setQueryData(['events'], [row, { ...row, id: 'two', source: 'phivolcs', place_name: 'PH event' }]);
    render(<QueryClientProvider client={client}><Feed /></QueryClientProvider>);
    expect(screen.getByText(/USGS event/)).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Event source'), { target: { value: 'phivolcs' } });
    expect(screen.queryByText(/USGS event/)).toBeNull();
    expect(screen.getByText(/PH event/)).toBeTruthy();
    await act(async () => {
      client.setQueryData(['events'], [{ ...row, id: 'three', source: 'phivolcs', place_name: 'New event' }]);
      await new Promise((resolve) => setTimeout(resolve, 10));
    });
    expect(screen.getByText(/New event/)).toBeTruthy();
    expect(screen.queryByText(/PH event/)).toBeNull();
  });
  it('distinguishes live transport from reconnecting and labels the last received time', () => {
    const view = render(<RealtimeStatus connected={false} lastUpdated={null} />);
    expect(screen.getByText(/Reconnecting/)).toBeTruthy();
    view.rerender(<RealtimeStatus connected lastUpdated="2026-08-29T09:30:00Z" />);
    expect(screen.getByText('LIVE')).toBeTruthy();
    expect(screen.getByText(/Last update/)).toBeTruthy();
  });
});
