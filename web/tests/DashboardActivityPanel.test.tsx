import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import DashboardActivityPanel from '../src/components/dashboard/DashboardActivityPanel';

describe('DashboardActivityPanel', () => {
  it('keeps notification and recent-event shortcuts available when collapsed', () => {
    const onToggleCollapsed = vi.fn();
    const onSelectTab = vi.fn();
    render(
      <DashboardActivityPanel
        collapsed
        unreadCount={3}
        activeTab="events"
        onToggleCollapsed={onToggleCollapsed}
        onSelectTab={onSelectTab}
      >
        <div>Activity content</div>
      </DashboardActivityPanel>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Expand activity panel' }));
    fireEvent.click(screen.getByRole('button', { name: 'Notifications, 3 unread' }));

    expect(onToggleCollapsed).toHaveBeenCalledTimes(2);
    expect(onSelectTab).toHaveBeenCalledWith('notifications');
  });

  it('shows accessible tabs and preserves its children while expanded', () => {
    render(
      <DashboardActivityPanel
        collapsed={false}
        unreadCount={0}
        activeTab="notifications"
        onToggleCollapsed={vi.fn()}
        onSelectTab={vi.fn()}
      >
        <div>Notification content</div>
      </DashboardActivityPanel>,
    );

    expect(screen.getByRole('tab', { name: 'Notifications' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByText('Notification content')).toBeInTheDocument();
  });
});
