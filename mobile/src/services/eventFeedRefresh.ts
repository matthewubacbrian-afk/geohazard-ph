import { loadEventFeed } from './eventFeed';
import type { EventFeedResult } from './eventFeed';

export type EventFeedRefreshHandlers = {
  onStart: () => void;
  onSuccess: (feed: EventFeedResult) => void;
  onError: (error: unknown) => void;
  onFinish: () => void;
};

export function createEventFeedRefreshController(
  loadFeed: (baseUrl: string) => Promise<EventFeedResult> = loadEventFeed,
) {
  let latestRequest = 0;

  return {
    async refresh(baseUrl: string, handlers: EventFeedRefreshHandlers): Promise<void> {
      const request = ++latestRequest;
      handlers.onStart();
      try {
        const feed = await loadFeed(baseUrl);
        if (request === latestRequest) handlers.onSuccess(feed);
      } catch (error) {
        if (request === latestRequest) handlers.onError(error);
      } finally {
        if (request === latestRequest) handlers.onFinish();
      }
    },
    invalidate(): void {
      latestRequest += 1;
    },
  };
}
