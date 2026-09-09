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
});