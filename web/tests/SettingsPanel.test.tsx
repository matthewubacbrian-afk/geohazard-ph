import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';

import SettingsPanel from '../src/components/common/SettingsPanel';

afterEach(cleanup);

describe('SettingsPanel', () => {
  it('closes from both the close icon and the done action', () => {
    const onClose = vi.fn();
    render(<SettingsPanel onClose={onClose} />);

    expect(screen.getByRole('dialog')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /close settings/i }));
    fireEvent.click(screen.getByRole('button', { name: /done/i }));

    expect(onClose).toHaveBeenCalledTimes(2);
  });

  it('moves keyboard focus into the dialog and closes with Escape', () => {
    const onClose = vi.fn();
    render(<SettingsPanel onClose={onClose} />);

    const closeButton = screen.getByRole('button', { name: /close settings/i });
    const dialog = screen.getByRole('dialog');
    const link = document.createElement('a');
    link.href = '#inside-settings';
    link.textContent = 'Settings help';
    const input = document.createElement('input');
    input.setAttribute('aria-label', 'Display preference');
    const outsideButton = document.createElement('button');
    outsideButton.textContent = 'Outside dialog';
    document.body.append(outsideButton);
    const doneButton = screen.getByRole('button', { name: /done/i });
    dialog.insertBefore(link, doneButton);
    dialog.insertBefore(input, doneButton);

    outsideButton.focus();
    expect(closeButton).toHaveFocus();

    fireEvent.keyDown(closeButton, { key: 'Tab' });
    expect(link).toHaveFocus();
    fireEvent.keyDown(link, { key: 'Tab' });
    expect(input).toHaveFocus();
    fireEvent.keyDown(input, { key: 'Tab' });
    expect(doneButton).toHaveFocus();
    fireEvent.keyDown(doneButton, { key: 'Tab' });
    expect(closeButton).toHaveFocus();
    fireEvent.keyDown(closeButton, { key: 'Tab', shiftKey: true });
    expect(doneButton).toHaveFocus();
    fireEvent.keyDown(doneButton, { key: 'Tab', shiftKey: true });
    expect(input).toHaveFocus();
    fireEvent.keyDown(input, { key: 'Tab', shiftKey: true });
    expect(link).toHaveFocus();
    fireEvent.keyDown(link, { key: 'Tab', shiftKey: true });
    expect(closeButton).toHaveFocus();
    fireEvent.keyDown(dialog, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledOnce();
    outsideButton.remove();
  });
});
