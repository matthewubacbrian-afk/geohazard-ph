import styles from './EventFilterBar.module.css';

export default function EventFilterBar({ source, onChange }: {
  source: string; onChange: (source: string) => void;
}) {
  return (
    <label className={styles.filter}>
      Event source
      <select value={source} onChange={(event) => onChange(event.target.value)}>
        <option value="">All sources</option>
        <option value="usgs">USGS</option>
        <option value="phivolcs">PHIVOLCS</option>
      </select>
    </label>
  );
}
