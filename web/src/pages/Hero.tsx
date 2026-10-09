import styles from "./Hero.module.css";
import Reveal from "../components/common/Reveal/Reveal";
import SectionHeader from "../components/common/SectionHeader";
import TopNav from "../components/layout/TopNav";
import type { View } from "../types/views";

type HeroProps = {
  onNavigate?: (view: View) => void;
  onSettings?: () => void;
};

const navItems = ["Dashboard", "How It Works", "About", "Data Sources", "Historical"];

const steps = [
  {
    title: "1. Historical Data",
    description:
      "Earthquake and volcano observations retain their source, time, and geographic context.",
  },
  {
    title: "2. K-Means Clustering",
    description:
      "Clustering groups regions with similar historical seismic characteristics.",
  },
  {
    title: "3. Random Forest",
    description:
      "Model outputs summarize historical features; they do not predict future earthquakes.",
  },
  {
    title: "4. LGU Dashboard",
    description:
      "Maps and source context support local review and planning alongside official guidance.",
  },
];

export default function Hero({ onNavigate, onSettings }: HeroProps) {
  return (
    <main className={styles.page}>
      <TopNav
        items={navItems}
        activeItem="How It Works"
        onNavigate={onNavigate}
        onSettings={onSettings}
        theme="hero"
      />

      <section className={styles.heroSection}>
        <div className={styles.heroContent}>
          <Reveal delayMs={0}>
            <h1 className={styles.heroTitle}>
              <span>Public hazard data for informed local planning</span>
            </h1>
          </Reveal>

          <Reveal delayMs={100}>
            <p className={styles.heroSubtitle}>
              Explore earthquake observations, volcano information, reference layers,
              and regional profiles with their source context.
            </p>
          </Reveal>

          <Reveal delayMs={200}>
            <div className={styles.heroActions}>
              <button
                type="button"
                className="primary-button"
                onClick={() => onNavigate?.("dashboard")}
              >
                View Risk Map
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={() => onNavigate?.("dashboard")}
              >
                View Dashboard
              </button>
            </div>
          </Reveal>
        </div>
      </section>

      <section className={styles.howItWorks}>
        <div className={styles.sectionInner}>
          <SectionHeader
            title="Methodology &amp; Pipeline"
            subtitle="How public observations and historical features are organized for review."
          />

          <div className={styles.processGrid}>
            <div className={styles.processLine} aria-hidden="true" />

            {steps.map((step, index) => (
              <Reveal key={step.title} delayMs={index * 100} className={styles.processCardWrap}>
                <article className={styles.processCard}>
                  <div className={styles.processIcon} aria-hidden="true">
                    {String(index + 1).padStart(2, "0")}
                  </div>
                  <h3 className={styles.processTitle}>{step.title}</h3>
                  <p className={styles.processDesc}>{step.description}</p>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.aboutSection}>
        <div className={styles.aboutGrid}>
          <div className={`${styles.aboutPanel} ${styles.aboutWide}`}>
            <h2 className={styles.aboutWideTitle}>Empowering Disaster Coordinators</h2>
            <p>
              GeoHazard brings public geohazard observations and reference information
              together to support review by local disaster risk reduction offices.
            </p>
            <p>
              Regional risk profiles describe historical patterns in available data
              and should be considered alongside current guidance from official authorities.
            </p>
            <p>Risk profiles are descriptive statistics, not earthquake predictions.</p>
          </div>
          <aside className={`${styles.aboutPanel} ${styles.aboutNotice}`}>
            <p>GeoHazard PH is not an official PHIVOLCS/NDRRMC advisory.</p>
            <p>Check official sources for current warnings and response instructions.</p>
          </aside>
        </div>
      </section>

      <footer className={styles.footer}>
        <div className={styles.footerInner}>
          <div className={styles.footerBrand}>
            <div className={styles.footerLogo}>GeoHazard</div>
            <p className={styles.footerTagline}>
              Public geohazard information for local review.
            </p>
          </div>

          <div className={styles.footerLinks}>
            {[
              ["About Project", "about"],
              ["Data Credits", "data-sources"],
            ].map(([item, target]) => (
              <a
                key={item}
                href="#"
                onClick={(event) => {
                  event.preventDefault();
                  onNavigate?.(target as View);
                }}
              >
                {item}
              </a>
            ))}
          </div>
        </div>
      </footer>
    </main>
  );
}
