import { LANDSLIDE_IMAGE_SERVICE, LANDSLIDE_OVERLAY_SOURCE_URL } from './landslideOverlays';
import type { LandslideOverlayState } from './landslideOverlays';
import styles from './StaticLayerStatus.module.css';
import legendStyles from './LandslideOverlayStatus.module.css';

type LandslideOverlayStatusProps = {
  state: LandslideOverlayState;
  onRetry: () => void;
};

export default function LandslideOverlayStatus({ state, onRetry }: LandslideOverlayStatusProps) {
  return <section className={styles.panel} aria-label="NASA landslide susceptibility reference layer">
    <strong>NASA Global Landslide Susceptibility Map</strong>
    {state === 'loading' ? <p role="status">Loading NASA landslide susceptibility reference…</p> :
      state === 'error' ? <p role="alert">
        NASA landslide susceptibility reference unavailable. <button type="button" onClick={onRetry}>Retry</button>
      </p> : <p role="status">NASA landslide susceptibility reference loaded.</p>}
    <p className={legendStyles.legend} aria-label="Susceptibility values from Low 0 to High 5">
      <span>Low · 0</span><span aria-hidden="true">—</span><span>High · 5</span>
    </p>
    <p><a href={LANDSLIDE_OVERLAY_SOURCE_URL} target="_blank" rel="noreferrer">
      Source: NASA Global Landslide Susceptibility Map
    </a></p>
    <small className={legendStyles.caveat}>
      Coarse, informational susceptibility reference for awareness; not an early-warning authority or site-level assessment.
      NASA notes it may be research-grade and unsuitable for operational use. Missing pixels do not mean low susceptibility.
    </small>
    <a className={legendStyles.serviceLink} href={LANDSLIDE_IMAGE_SERVICE} target="_blank" rel="noreferrer">
      View NASA image service
    </a>
  </section>;
}
