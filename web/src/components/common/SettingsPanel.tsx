import { useEffect, useRef } from 'react';

import { API_BASE_URL } from '../../api/client';
import styles from './SettingsPanel.module.css';

type SettingsPanelProps = {
  onClose: () => void;
};

export default function SettingsPanel({ onClose }: SettingsPanelProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const previouslyFocused = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null;
    const keepFocusInside = (event: FocusEvent) => {
      if (event.target instanceof Node && !panelRef.current?.contains(event.target)) {
        closeButtonRef.current?.focus();
      }
    };

    document.addEventListener('focusin', keepFocusInside);
    closeButtonRef.current?.focus();
    return () => {
      document.removeEventListener('focusin', keepFocusInside);
      previouslyFocused?.focus();
    };
  }, []);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLElement>) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      onClose();
      return;
    }
    if (event.key !== 'Tab') return;

    const candidates = event.currentTarget.querySelectorAll<HTMLElement>(
      'a[href], area[href], input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), iframe, object, embed, [contenteditable="true"], [tabindex]:not([tabindex="-1"])',
    );
    const focusable = Array.from(candidates).filter((element) => {
      const style = window.getComputedStyle(element);
      return element.tabIndex >= 0 &&
        !element.closest('[hidden], [inert], [aria-hidden="true"]') &&
        style.display !== 'none' &&
        style.visibility !== 'hidden';
    });
    if (focusable.length === 0) return;

    const currentIndex = focusable.indexOf(document.activeElement as HTMLElement);
    const direction = event.shiftKey ? -1 : 1;
    const nextIndex = (currentIndex + direction + focusable.length) % focusable.length;
    event.preventDefault();
    focusable[nextIndex]?.focus();
  };

  return (
    <div className={styles.backdrop} role="presentation" onClick={onClose}>
      <section
        ref={panelRef}
        className={styles.panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
        onClick={(event) => event.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        <div className={styles.header}>
          <div>
            <p className={styles.eyebrow}>Application</p>
            <h2 id="settings-title">Settings</h2>
          </div>
          <button ref={closeButtonRef} type="button" className={styles.close} onClick={onClose} aria-label="Close settings">
            <svg aria-hidden="true" viewBox="0 0 20 20" width="20" height="20" fill="none">
              <path d="m5 5 10 10M15 5 5 15" stroke="currentColor" strokeWidth="1.7" />
            </svg>
          </button>
        </div>
        <dl className={styles.details}>
          <dt>API endpoint</dt>
          <dd>{API_BASE_URL}</dd>
          <dt>Refresh interval</dt>
          <dd>30 seconds</dd>
        </dl>
        <button type="button" className={styles.done} onClick={onClose}>Done</button>
      </section>
    </div>
  );
}
