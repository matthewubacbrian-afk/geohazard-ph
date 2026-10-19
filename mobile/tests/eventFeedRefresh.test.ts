import { createEventFeedRefreshController } from '../src/services/eventFeedRefresh';
import type { EventFeedResult } from '../src/services/eventFeed';

jest.mock('../src/services/eventFeed', () => ({ loadEventFeed: jest.fn() }));

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function handlers() {
  return {
    onStart: jest.fn(),
    onSuccess: jest.fn(),
    onError: jest.fn(),
    onFinish: jest.fn(),
  };
}

const olderFeed: EventFeedResult = { events: [], isOffline: true };
const newerFeed: EventFeedResult = { events: [], isOffline: false };

describe('mobile event-feed refresh ordering', () => {
  it('applies only the newest success when responses arrive out of order', async () => {
    const older = deferred<EventFeedResult>();
    const newer = deferred<EventFeedResult>();
    const loadFeed = jest.fn()
      .mockReturnValueOnce(older.promise)
      .mockReturnValueOnce(newer.promise);
    const controller = createEventFeedRefreshController(loadFeed);
    const oldHandlers = handlers();
    const newHandlers = handlers();

    const oldRequest = controller.refresh('https://example.org/api/v1', oldHandlers);
    const newRequest = controller.refresh('https://example.org/api/v1', newHandlers);
    newer.resolve(newerFeed);
    await newRequest;
    older.resolve(olderFeed);
    await oldRequest;

    expect(oldHandlers.onStart).toHaveBeenCalledTimes(1);
    expect(oldHandlers.onSuccess).not.toHaveBeenCalled();
    expect(oldHandlers.onError).not.toHaveBeenCalled();
    expect(oldHandlers.onFinish).not.toHaveBeenCalled();
    expect(newHandlers.onSuccess).toHaveBeenCalledWith(newerFeed);
    expect(newHandlers.onFinish).toHaveBeenCalledTimes(1);
  });

  it('ignores an older error after a newer refresh succeeds', async () => {
    const older = deferred<EventFeedResult>();
    const newer = deferred<EventFeedResult>();
    const loadFeed = jest.fn()
      .mockReturnValueOnce(older.promise)
      .mockReturnValueOnce(newer.promise);
    const controller = createEventFeedRefreshController(loadFeed);
    const oldHandlers = handlers();
    const newHandlers = handlers();

    const oldRequest = controller.refresh('https://example.org/api/v1', oldHandlers);
    const newRequest = controller.refresh('https://example.org/api/v1', newHandlers);
    newer.resolve(newerFeed);
    await newRequest;
    older.reject(new Error('old network error'));
    await oldRequest;

    expect(oldHandlers.onError).not.toHaveBeenCalled();
    expect(oldHandlers.onFinish).not.toHaveBeenCalled();
    expect(newHandlers.onSuccess).toHaveBeenCalledWith(newerFeed);
  });

  it('invalidates a request when the selected API server changes', async () => {
    const pending = deferred<EventFeedResult>();
    const controller = createEventFeedRefreshController(() => pending.promise);
    const callbacks = handlers();

    const request = controller.refresh('https://old.example/api/v1', callbacks);
    controller.invalidate();
    pending.resolve(olderFeed);
    await request;

    expect(callbacks.onStart).toHaveBeenCalledTimes(1);
    expect(callbacks.onSuccess).not.toHaveBeenCalled();
    expect(callbacks.onError).not.toHaveBeenCalled();
    expect(callbacks.onFinish).not.toHaveBeenCalled();
  });

  it('delivers the current failure and completes its loading state', async () => {
    const error = new Error('network error');
    const controller = createEventFeedRefreshController(async () => { throw error; });
    const callbacks = handlers();

    await controller.refresh('https://example.org/api/v1', callbacks);

    expect(callbacks.onError).toHaveBeenCalledWith(error);
    expect(callbacks.onSuccess).not.toHaveBeenCalled();
    expect(callbacks.onFinish).toHaveBeenCalledTimes(1);
  });
});
