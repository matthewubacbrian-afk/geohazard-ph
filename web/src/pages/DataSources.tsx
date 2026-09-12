import TopNav from "../components/layout/TopNav";
import type { View } from "../types/views";
import styles from "./InformationalPage.module.css";

const navItems = ["Dashboard", "How It Works", "About", "Data Sources", "Historical", "Contact"];

type DataSourcesProps = {
  onNavigate?: (view: View) => void;
  onSettings?: () => void;
};

export default function DataSources({ onNavigate, onSettings }: DataSourcesProps) {
  return (
    <main className={styles.page}>
      <TopNav items={navItems} activeItem="Data Sources" onNavigate={onNavigate} onSettings={onSettings} />
      <div className={styles.content}>
        <header className={styles.intro}>
          <p className={styles.eyebrow}>Provenance and attribution</p>
          <h1 className={styles.title}>Data Sources</h1>
          <p className={styles.lead}>
            GeoHazard preserves provider names, timestamps, coordinates, and source context
            so every view can be understood and checked.
          </p>
        </header>
        <div className={styles.grid}>
          <section className={styles.panel}>
            <h2>Observed hazards</h2>
            <ul>
              <li>USGS Earthquake Catalog for earthquake observations.</li>
              <li>PHIVOLCS bulletins for Philippine earthquake and volcano information.</li>
              <li>Smithsonian Global Volcanism Program reference data for volcanoes.</li>
            </ul>
          </section>
          <section className={styles.panel}>
            <h2>Reference layers</h2>
            <ul>
              <li>GEM Global Active Faults Database for fault-line references.</li>
              <li>PHIVOLCS GIS material where reviewed and permissioned for use.</li>
              <li>Source licensing and attribution are documented before redistribution.</li>
            </ul>
          </section>
        </div>
      </div>
    </main>
  );
}
