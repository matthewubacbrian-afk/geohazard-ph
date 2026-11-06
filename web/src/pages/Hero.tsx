import TopNav from "../components/layout/TopNav";
import type { View } from "../types/views";
import styles from "./InformationalPage.module.css";
import guide from "./ProjectGuide.module.css";

const navItems = ["Dashboard", "Scene Review", "How It Works", "About", "Data Sources", "Historical"];
const steps = [
  { title: "Collect observations", text: "Public USGS and PHIVOLCS earthquake reports are imported periodically. Staging refreshes run every six hours, so new reports may take time to appear." },
  { title: "Keep the context", text: "Records retain their source, event time, location, and magnitude. Matching reports are organized into a shared event view to reduce duplicate observations." },
  { title: "Explore the map", text: "Filter available records by source, date, and magnitude. Compare event markers with geographic references and recorded regional activity." },
];
type HeroProps = { onNavigate?: (view: View) => void; onSettings?: () => void };

export default function Hero({ onNavigate, onSettings }: HeroProps) {
  return <main className={styles.page}>
    <TopNav items={navItems} activeItem="How It Works" theme="dashboard" onNavigate={onNavigate} onSettings={onSettings} />
    <div className={styles.content}>
      <header className={styles.intro}>
        <p className={styles.eyebrow}>How it works / A guide to the project</p>
        <h1 className={styles.title}>Public hazard data for informed local planning</h1>
        <p className={styles.lead}>Follow recorded events, understand the map, and review visual scene cues—with sources and limitations in view.</p>
        <div className={styles.actions}><a className={styles.action} href="/dashboard">Explore the dashboard</a></div>
      </header>
      <section className={guide.feature} aria-labelledby="approach-title">
        <div><p className={guide.kicker}>One place. Three ways to explore.</p><h2 id="approach-title">Observe.<br />Understand.<br />Review.</h2></div>
        <div><p>GeoHazard PH connects public observations with geographic context. The dashboard helps visitors ask where an event was recorded, when it happened, and which source reported it.</p><p>Scene Review adds a separate, on-device view of visible objects and ground cues. Both experiences support awareness; official authorities remain the source for warnings and response instructions.</p></div>
      </section>
      <section className={guide.section} aria-labelledby="flow-title">
        <header className={guide.sectionHeader}><div><p className={styles.eyebrow}>01 / The observation flow</p><h2 id="flow-title">From source to screen</h2></div><p>A periodically refreshed collection, with the original reporting context preserved.</p></header>
        <ol className={`${guide.grid} ${guide.threeColumns} ${guide.steps}`}>
          {steps.map((step, index) => <li className={guide.card} key={step.title}><span className={guide.stepNumber}>0{index + 1}</span><h3>{step.title}</h3><p>{step.text}</p></li>)}
        </ol>
      </section>
      <section className={guide.section} aria-labelledby="reading-title">
        <header className={guide.sectionHeader}><div><p className={styles.eyebrow}>02 / Read the map</p><h2 id="reading-title">Context behind the color</h2></div><p>Each layer answers a different question. Combine it with source dates and coverage.</p></header>
        <dl className={guide.factList}>
          <div><dt>Event markers</dt><dd>Marker size and color indicate reported magnitude where available. An epicenter marks an event location, not its full area of impact.</dd></div>
          <div><dt>Activity shading</dt><dd>Regions are shaded by recorded earthquake counts for the selected filters. Offshore or outside-boundary records remain unassigned. Counts describe available reports, not seismic risk.</dd></div>
          <div><dt>Reference layers</dt><dd>Fault lines and other reference layers add geographic context. Their coverage, scale, and publication dates differ from the event feeds.</dd></div>
          <div><dt>Freshness</dt><dd>The LIVE indicator describes the dashboard connection. Check event timestamps and source updates to judge how current the observations are.</dd></div>
        </dl>
      </section>
      <section className={guide.grid} aria-label="Scene review and research">
        <article className={guide.card}><span className={guide.tag}>03 / Available on the web</span><h2>Scene review on your device</h2><p>Choose a photo to inspect visible objects and simplified ground candidates. Analysis runs in your browser; the photo is not uploaded for inference.</p><p>The first use downloads model files and runtime resources. Visual cues can be incomplete or mistaken and cannot determine whether a place or structure is safe.</p><div className={guide.cardLinks}><a className={guide.link} href="/scene-analysis">Try Scene Review</a></div></article>
        <article id="research" className={guide.card}><span className={guide.tag}>Research / Under review</span><h2>Historical modeling</h2><p>Model exports remain under review and are not published as approved risk guidance.</p><p>The current regional display uses recorded activity counts rather than unapproved Low, Moderate, or High labels.</p><p>Risk profiles are descriptive statistics, not earthquake predictions.</p><details className={guide.details}><summary>About the research approach</summary><p>Offline experiments use historical seismic features, K-Means clustering, and Random Forest classification. Validation and source coverage must be assessed before any model-derived labels are released.</p></details></article>
      </section>
      <aside className={guide.note}><h2>Awareness with clear limits</h2><p>GeoHazard PH is not an official PHIVOLCS/NDRRMC advisory. Check official sources for current warnings and response instructions.</p></aside>
      <footer className={guide.footer}><p>GeoHazard PH / Public information for local review.</p><div className={guide.footerLinks}><a className={guide.link} href="/about">About Project</a><a className={guide.link} href="/data-sources">Data Credits</a></div></footer>
    </div>
  </main>;
}
