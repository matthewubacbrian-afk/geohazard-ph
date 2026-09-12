import TopNav from "../components/layout/TopNav";
import type { View } from "../types/views";
import styles from "./InformationalPage.module.css";

const navItems = ["Dashboard", "How It Works", "About", "Data Sources", "Historical", "Contact"];

type HistoricalBrowserProps = {
  onNavigate?: (view: View) => void;
  onSettings?: () => void;
};

export default function HistoricalBrowser({ onNavigate, onSettings }: HistoricalBrowserProps) {
  return (
    <main className={styles.page}>
      <TopNav items={navItems} activeItem="Historical" onNavigate={onNavigate} onSettings={onSettings} />
      <div className={styles.content}>
        <header className={styles.intro}>
          <p className={styles.eyebrow}>Planned capability</p>
          <h1 className={styles.title}>Historical Event Browser</h1>
          <p className={styles.lead}>
            A future feature for comparing hazard activity across time, place, source, and
            event type.
          </p>
          <p className={styles.lead}>
            The Historical Browser is not available yet. This page explains the planned
            feature without presenting non-functional search controls.
          </p>
          <div className={styles.actions}>
            <a className={styles.action} href="/dashboard">Open live dashboard</a>
          </div>
        </header>
        <div className={styles.grid}>
          <section className={styles.panel}>
            <h2>Planned views</h2>
            <p>Time-range exploration, historical comparisons, and source-aware event context.</p>
          </section>
          <section className={styles.panel}>
            <h2>Current alternative</h2>
            <p>Use the live dashboard for current event feeds, filters, and available reference layers.</p>
          </section>
        </div>
      </div>
    </main>
  );
}
