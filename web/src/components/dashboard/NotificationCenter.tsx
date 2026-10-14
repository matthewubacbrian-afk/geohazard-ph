import { useState } from 'react';
import type { DashboardNotification } from '../../types/notification';
import styles from './NotificationCenter.module.css';

type Props = { notifications: DashboardNotification[]; onMarkRead: (id: string) => void; onMarkAllRead: () => void };
const dateTime = (value: string) => new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));

export default function NotificationCenter({ notifications, onMarkRead, onMarkAllRead }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const unread = notifications.some((item) => item.read_at === null);
  return <section className={styles.center} aria-label="Notifications">
    <div className={styles.heading}><div><h2>Notifications</h2><p>Live hazard events received in this browser</p></div>
      {unread && <button type="button" onClick={onMarkAllRead}>Mark all read</button>}</div>
    {notifications.length === 0 ? <p className={styles.empty}>No realtime notifications yet</p> : <ul className={styles.list}>
      {notifications.map((item) => {
        const open = expanded === item.id;
        const event = item.event;
        return <li key={item.id} className={`${styles.item} ${item.read_at === null ? styles.unread : ''}`}>
          <button type="button" className={styles.itemButton} aria-expanded={open} onClick={() => {
            setExpanded(open ? null : item.id);
            if (item.read_at === null) onMarkRead(item.id);
          }}>
            <span className={styles.dot} aria-hidden="true"/><span className={styles.summary}><strong>{event.place_name}</strong><span>{event.hazard_type}</span></span>
            <span className={styles.meta}><strong>M{event.magnitude ?? '—'}</strong><span>{dateTime(item.received_at)}</span><span className={styles.source}>{event.source.toUpperCase()}</span></span>
            <span className={styles.chevron} aria-hidden="true">{open ? '−' : '+'}</span>
          </button>
          {open && <div className={styles.details}><p>{event.hazard_type === 'earthquake' ? 'Earthquake' : event.hazard_type} event recorded {dateTime(event.occurred_at)}.</p>
            <dl><div><dt>Magnitude</dt><dd>{event.magnitude ?? '—'}</dd></div><div><dt>Depth</dt><dd>{event.depth_km == null ? 'Not reported' : `${event.depth_km} km`}</dd></div>
              <div><dt>Coordinates</dt><dd>{event.latitude.toFixed(2)}, {event.longitude.toFixed(2)}</dd></div><div><dt>Source</dt><dd>{event.source.toUpperCase()}</dd></div></dl></div>}
        </li>;
      })}
    </ul>}
    <p className={styles.note}>Notifications are saved only in this browser. They begin when live events arrive; historical query results are not added.</p>
  </section>;
}
