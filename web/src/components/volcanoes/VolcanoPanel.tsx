import { useVolcanoes } from '../../hooks/useVolcanoes';
import Skeleton from '../common/Skeleton';
import styles from './VolcanoPanel.module.css';

export default function VolcanoPanel() {
  const { data = [], isLoading, error, refetch } = useVolcanoes();
  return (
    <section className={styles.panel} aria-label="Volcano bulletins">
      <h2>Volcano activity</h2>
      <p>PHIVOLCS bulletins · Unofficial aggregation</p>
      {isLoading && <div role="status"><Skeleton width="100%" height={80} />Loading volcano bulletins…</div>}
      {error && <div role="alert">
        <p>Volcano bulletins temporarily unavailable.</p>
        <button type="button" onClick={() => refetch()}>Retry</button>
      </div>}
      {!isLoading && !error && !data.length && <p>No volcano bulletins are available yet.</p>}
      {!error && data.map((volcano) => (
        <article className={styles.bulletin} key={volcano.id}>
          <h3>{volcano.name}</h3>
          <strong>{volcano.current_alert_level !== null
            ? `Alert Level ${volcano.current_alert_level}` : 'Alert level not supplied'}</strong>
          {volcano.stale && <p role="status">Cached source — refresh temporarily unavailable.</p>}
          <p>{volcano.bulletin_at
            ? `Bulletin observation: ${new Date(volcano.bulletin_at).toLocaleString()}`
            : 'Bulletin date not supplied by the source.'}</p>
          {volcano.retrieved_at && <p>Retrieved {new Date(volcano.retrieved_at).toLocaleString()}</p>}
          {(volcano.bulletin_url || volcano.source_url) && (
            <a href={volcano.bulletin_url ?? volcano.source_url ?? undefined}
              target="_blank" rel="noreferrer">Read PHIVOLCS source</a>
          )}
        </article>
      ))}
    </section>
  );
}
