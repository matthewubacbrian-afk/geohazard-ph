import styles from './RealtimeStatus.module.css';

type Props = { connected: boolean; lastUpdated: string | null };

export default function RealtimeStatus({ connected, lastUpdated }: Props) {
  return (
    <div className={`${styles.status} ${connected ? styles.connected : styles.disconnected}`} role="status">
      <div className={styles.transport}>
        <strong>{connected ? 'LIVE' : 'Reconnecting — periodic refresh active'}</strong>
        {lastUpdated && <time dateTime={lastUpdated}>Last update {new Date(lastUpdated).toLocaleTimeString()}</time>}
      </div>
      <p className={styles.advisory}>GeoHazard PH is not an official PHIVOLCS/NDRRMC advisory</p>
    </div>
  );
}
