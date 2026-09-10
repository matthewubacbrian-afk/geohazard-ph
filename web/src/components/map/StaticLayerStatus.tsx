import type { StaticLayer } from '../../types/staticLayer';
import styles from './StaticLayerStatus.module.css';

type Props = {
  label: string;
  rows: StaticLayer[] | undefined;
  loading: boolean;
  error: Error | null;
  onRetry: () => void;
};

export default function StaticLayerStatus({ label, rows, loading, error, onRetry }: Props) {
  const sources = [...new Map((rows ?? []).map(row => [
    `${row.source_url}:${row.dataset_version}`, row,
  ])).values()];
  return <section className={styles.panel} aria-label={`${label} reference layer`}>
    <strong>{label}</strong>
    {loading ? <p role="status">Loading {label.toLowerCase()}…</p> : error ?
      <p role="alert">Could not load {label.toLowerCase()}. <button onClick={onRetry}>Retry</button></p> :
      !rows?.length ? <p>No {label.toLowerCase()} imported yet.</p> : <>
        <p>{rows.length} reference features. {label === 'Fault lines' ? 'Solid lines' : 'Shaded polygons'} on the map.</p>
        {sources.map(row => <p key={`${row.source_url}:${row.dataset_version}`}>
          <a href={row.source_url} target="_blank" rel="noreferrer">{row.source.toUpperCase()}</a>
          {' · '}{row.dataset_version}{' · '}{row.license_name}
        </p>)}
      </>}
    <small>Static reference data; consult official maps for site assessments.</small>
  </section>;
}
