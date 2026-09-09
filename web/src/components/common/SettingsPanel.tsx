import { API_BASE_URL } from '../../api/client';
import styles from './SettingsPanel.module.css';

type SettingsPanelProps = {
  onClose: () => void;
};

export default function SettingsPanel({ onClose }: SettingsPanelProps) {
  return (
    <div className={styles.backdrop} role="presentation" onClick={onClose}>
      <section
        className={styles.panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className={styles.header}>
          <div>
            <p className={styles.eyebrow}>Application</p>
            <h2 id="settings-title">Settings</h2>
          </div>
          <button type="button" className={styles.close} onClick={onClose} aria-label="Close settings">
            <span aria-hidden="true">×</span>
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
