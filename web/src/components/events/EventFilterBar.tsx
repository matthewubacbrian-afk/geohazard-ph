import styles from './EventFilterBar.module.css';

export default function EventFilterBar({ source, onChange }: {
  source: string; onChange: (source: string) => void;
}) {
  const sources = [
    { value: '', label: 'All sources' },
    { value: 'usgs', label: 'USGS' },
    { value: 'phivolcs', label: 'PHIVOLCS' },
  ];

  return (
    <fieldset className={styles.filter}>
      <legend>Source</legend>
      <div className={styles.options} role="group" aria-label="Event source">
        {sources.map((item) => (
          <button
            key={item.value || 'all'}
            type="button"
            className={`${styles.option} ${source === item.value ? styles.active : ''}`}
            aria-pressed={source === item.value}
            onClick={() => onChange(item.value)}
          >
            {item.label === 'All sources' ? 'All' : item.label}
          </button>
        ))}
      </div>
    </fieldset>
  );
}
