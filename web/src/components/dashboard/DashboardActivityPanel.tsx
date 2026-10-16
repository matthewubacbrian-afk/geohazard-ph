import type { ReactNode } from 'react';
import Icon from '../common/Icon';
import styles from './DashboardActivityPanel.module.css';

export type ActivityTab = 'events' | 'notifications';
type Props = { collapsed: boolean; unreadCount: number; activeTab: ActivityTab; onToggleCollapsed: () => void; onSelectTab: (tab: ActivityTab) => void; children: ReactNode };

export default function DashboardActivityPanel({ collapsed, unreadCount, activeTab, onToggleCollapsed, onSelectTab, children }: Props) {
  if (collapsed) return <aside className={`${styles.panel} ${styles.collapsed}`} aria-label="Activity panel">
    <button type="button" className={styles.railToggle} aria-label="Expand activity panel" onClick={onToggleCollapsed}>‹</button>
    <button type="button" className={styles.railButton} aria-label="Recent events" title="Recent events" onClick={() => { onSelectTab('events'); onToggleCollapsed(); }}><span aria-hidden="true">≋</span></button>
    <button type="button" className={`${styles.railButton} ${unreadCount ? styles.hasUnread : ''}`} aria-label={unreadCount ? `Notifications, ${unreadCount} unread` : 'Notifications'} title="Notifications" onClick={() => { onSelectTab('notifications'); onToggleCollapsed(); }}>
      <Icon name="bell" />{unreadCount > 0 && <span className={styles.badge} aria-hidden="true">{unreadCount > 99 ? '99+' : unreadCount}</span>}
    </button>
  </aside>;
  return <aside className={styles.panel} aria-label="Activity panel">
    <header className={styles.header}><div className={styles.tabs} role="tablist" aria-label="Dashboard activity">
      <button type="button" role="tab" aria-selected={activeTab === 'events'} onClick={() => onSelectTab('events')}>Recent events</button>
      <button type="button" role="tab" aria-selected={activeTab === 'notifications'} onClick={() => onSelectTab('notifications')}>
        Notifications{unreadCount > 0 && <span className={styles.tabBadge}>{unreadCount > 99 ? '99+' : unreadCount}</span>}
      </button>
    </div><button type="button" className={styles.collapse} aria-label="Collapse activity panel" onClick={onToggleCollapsed}>›</button></header>
    <div className={styles.content}>{children}</div>
  </aside>;
}
