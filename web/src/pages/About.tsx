import TopNav from "../components/layout/TopNav";
import type { View } from "../types/views";
import styles from "./InformationalPage.module.css";

const navItems = ["Dashboard", "How It Works", "About", "Data Sources", "Historical", "Contact"];

type AboutProps = {
  onNavigate?: (view: View) => void;
  onSettings?: () => void;
};

export default function About({ onNavigate, onSettings }: AboutProps) {
  return (
    <main className={styles.page}>
      <TopNav items={navItems} activeItem="About" onNavigate={onNavigate} onSettings={onSettings} />
      <div className={styles.content}>
        <header className={styles.intro}>
          <p className={styles.eyebrow}>About the project</p>
          <h1 className={styles.title}>About GeoHazard</h1>
          <p className={styles.lead}>
            GeoHazard turns public geohazard observations into a clear working view for
            Philippine local governance and disaster-response teams.
          </p>
        </header>
        <div className={styles.grid}>
          <section className={styles.panel}>
            <h2>What it brings together</h2>
            <p>
              The dashboard combines earthquake events, active-fault references, volcano
              information, and regional risk profiles in one place.
            </p>
          </section>
          <section className={styles.panel}>
            <h2>How to read risk profiles</h2>
            <p>
              Risk profiles summarize historical records. They are descriptive statistical
              profiles rather than predictions, forecasts, or official warnings.
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}
