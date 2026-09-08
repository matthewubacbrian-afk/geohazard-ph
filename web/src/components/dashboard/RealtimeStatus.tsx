import styles from './RealtimeStatus.module.css';

type Props = { connected: boolean; lastUpdated: string | null };

export default function RealtimeStatus({ connected, lastUpdated }: Props) {
  return (
    <div className={styles.status} role="status">
      <strong>{connected ? 'LIVE' : 'Reconnecting — periodic refresh active'}</strong>
      {lastUpdated && <time dateTime={lastUpdated}>Last update {new Date(lastUpdated).toLocaleTimeString()}</time>}
    </div>
  );
}
