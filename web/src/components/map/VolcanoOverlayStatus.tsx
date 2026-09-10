import { VOLCANO_MAP_BASE, VOLCANO_OVERLAYS, type VolcanoOverlayState } from './volcanoOverlays';
import styles from './StaticLayerStatus.module.css';

export default function VolcanoOverlayStatus({ state, onRetry }: {
  state: VolcanoOverlayState;
  onRetry: () => void;
}) {
  return <section className={styles.panel} aria-label="Volcano zones reference layer">
    <strong>Volcano zones</strong>
    {state === 'error' ? <p role="alert">
      Some PHIVOLCS map layers could not load. <button onClick={onRetry}>Retry</button>
    </p> : state === 'loading' ? <p role="status">Loading PHIVOLCS hazard maps…</p> :
      <p>PHIVOLCS hazard maps loaded for this view. Zoom in near a volcano to see mapped zones.</p>}
    <p>Official reference overlays: {VOLCANO_OVERLAYS.map((layer, index) => <span key={layer.id}>
      {index > 0 && ' · '}
      <a href={`${VOLCANO_MAP_BASE}/${layer.service}/MapServer`} target="_blank" rel="noreferrer">
        {layer.label}
      </a>
    </span>)}</p>
    <small>Colors follow the source maps. These zones do not indicate current alert levels.</small>
  </section>;
}
