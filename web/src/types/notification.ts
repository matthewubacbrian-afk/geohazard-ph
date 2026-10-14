import type { EventChange } from './hazard';

export type DashboardNotification = {
  id: string;
  event: EventChange;
  received_at: string;
  read_at: string | null;
};
