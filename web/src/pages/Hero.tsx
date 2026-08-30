import styles from "./Hero.module.css";
import RiskMeter from "../components/common/RiskMeter";
import SectionHeader from "../components/common/SectionHeader";
import TopNav from "../components/layout/TopNav";
import type { View } from "../types/views";

type HeroProps = {
  onNavigate?: (view: View) => void;
};

const navItems = ["Dashboard", "How It Works", "About", "Data Sources", "Contact"];

const steps = [
  {
    title: "1. Historical Data",
    description:
      "Integration of PHIVOLCS & USGS seismic records for comprehensive baseline data.",
  },
  {
    title: "2. K-Means Clustering",
    description:
      "Spatial pattern identification to group regions with similar seismic characteristics.",
  },
  {
    title: "3. Random Forest",
    description:
      "Advanced machine learning classification for highly accurate risk probability scoring.",
  },
  {
    title: "4. LGU Dashboard",
    description:
      "Translation of complex models into actionable, localized insights for decision-makers.",
  },
];

export default function Hero({ onNavigate }: HeroProps) {
  return (
    <main className={styles.page}>
      <TopNav
        items={navItems}
        activeItem="How It Works"
        onNavigate={onNavigate}
        theme="hero"
      />

      <section className={styles.heroSection}>
        <div className={styles.heroOverlay} />
        <div className={styles.heroAbstract} aria-hidden="true" />

        <div className={styles.heroContent}>
          <h1 className={styles.heroTitle}>
            <span>Patterns.Predictions.Protection.</span>
            <span>Before the Ground Shakes</span>
          </h1>

          <p className={styles.heroSubtitle}>
            From fault lines to insights. From patterns to preparedness
          </p>

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
        </div>
      </section>

      <section className={styles.howItWorks}>
        <div className={styles.sectionInner}>
          <SectionHeader
            title="Methodology &amp; Pipeline"
            subtitle="A robust, scientific approach to risk classification."
          />

          <div className={styles.processGrid}>
            <div className={styles.processLine} aria-hidden="true" />

            {steps.map((step) => (
              <article key={step.title} className={styles.processCard}>
                <div className={styles.processIcon}>
                  <span aria-hidden="true">•</span>
                </div>
                <h3 className={styles.processTitle}>{step.title}</h3>
                <p className={styles.processDesc}>{step.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.aboutSection}>
        <div className={styles.aboutGrid}>
          <div className={`${styles.aboutPanel} ${styles.aboutWide}`}>
            <h2 className={styles.aboutWideTitle}>Empowering Disaster Coordinators</h2>
            <p>
              The primary objective of GeoHazard is to bridge the gap between
              complex geophysical data and pragmatic local governance. We equip
              LGU disaster risk reduction management offices with precise,
              localized intelligence.
            </p>
            <p>
              By moving away from generalized national maps to high-resolution,
              LGU-specific risk profiles, we enable targeted infrastructure
              reinforcement and optimized evacuation planning, ultimately
              mitigating potential casualties during seismic events.
            </p>
          </div>

          <div className={`${styles.aboutPanel} ${styles.aboutStats}`}>
            <RiskMeter label="High Risk" level="high" value={85} />
            <RiskMeter label="Moderate" level="medium" value={45} />
            <RiskMeter label="Low Risk" level="low" value={20} />
            <p className={styles.riskCaption}>Sample Risk Profiling Output</p>
          </div>
        </div>
      </section>

      <footer className={styles.footer}>
        <div className={styles.footerInner}>
          <div className={styles.footerBrand}>
            <div className={styles.footerLogo}>GeoHazard</div>
            <p className={styles.footerTagline}>
              © 2024 GeoHazard Philippines. Seismic Risk Intelligence for Local
              Governance.
            </p>
          </div>

          <div className={styles.footerLinks}>
            {[
              "About Project",
              "Data Credits",
              "Privacy Policy",
              "Contact Support",
            ].map((item) => (
              <a key={item} href="#">
                {item}
              </a>
            ))}
          </div>
        </div>
      </footer>
    </main>
  );
}
