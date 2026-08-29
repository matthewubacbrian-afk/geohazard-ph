import RiskMeter from "../components/common/RiskMeter";
import SectionHeader from "../components/common/SectionHeader";
import TopNav from "../components/layout/TopNav";

type HeroProps = {
  onNavigate?: (view: "dashboard") => void;
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
    <main className="hero-page">
      <TopNav
        items={navItems}
        activeItem="How It Works"
        onNavigate={onNavigate}
        theme="hero"
      />

      <section className="hero-section">
        <div className="hero-overlay" />
        <div className="hero-abstract" aria-hidden="true" />

        <div className="hero-content">
          <h1 className="hero-title">
            <span>Patterns.Predictions.Protection.</span>
            <span>Before the Ground Shakes</span>
          </h1>

          <p className="hero-subtitle">
            From fault lines to insights. From patterns to preparedness
          </p>

          <div className="hero-actions">
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

      <section className="how-it-works">
        <div className="section-inner">
          <SectionHeader
            title="Methodology &amp; Pipeline"
            subtitle="A robust, scientific approach to risk classification."
          />

          <div className="process-grid">
            <div className="process-line" aria-hidden="true" />

            {steps.map((step) => (
              <article key={step.title} className="process-card">
                <div className="process-icon">
                  <span aria-hidden="true">•</span>
                </div>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="about-section">
        <div className="about-grid">
          <div className="about-panel about-panel--wide">
            <h2>Empowering Disaster Coordinators</h2>
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

          <div className="about-panel about-panel--stats">
            <RiskMeter label="High Risk" level="high" value={85} />
            <RiskMeter label="Moderate" level="medium" value={45} />
            <RiskMeter label="Low Risk" level="low" value={20} />
            <p className="risk-caption">Sample Risk Profiling Output</p>
          </div>
        </div>
      </section>

      <footer className="site-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <div className="footer-logo">GeoHazard</div>
            <p>
              © 2024 GeoHazard Philippines. Seismic Risk Intelligence for Local
              Governance.
            </p>
          </div>

          <div className="footer-links">
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
