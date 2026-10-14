import { useCallback, useEffect, useState } from 'react';
import type { EventChange } from '../types/hazard';
import {
  addRealtimeNotification,
  loadNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  NOTIFICATION_STORAGE_KEY,
  persistNotifications,
} from '../lib/notifications';

export function useNotifications() {
  const [notifications, setNotifications] = useState(loadNotifications);

  useEffect(() => {
    persistNotifications(notifications);
  }, [notifications]);

  useEffect(() => {
    function handleStorage(event: StorageEvent) {
      if (event.key === NOTIFICATION_STORAGE_KEY) setNotifications(loadNotifications());
    }
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const addEvent = useCallback((event: EventChange) => {
    setNotifications((previous) => addRealtimeNotification(previous, event, new Date().toISOString()));
  }, []);
  const markRead = useCallback((id: string) => {
    setNotifications((previous) => markNotificationRead(previous, id));
  }, []);
  const markAllRead = useCallback(() => {
    setNotifications((previous) => markAllNotificationsRead(previous));
  }, []);

  return {
    notifications,
    unreadCount: notifications.filter((item) => item.read_at === null).length,
    addEvent,
    markRead,
    markAllRead,
  };
}
