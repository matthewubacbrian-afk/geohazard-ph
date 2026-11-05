import TopNav from "../components/layout/TopNav";
import type { View } from "../types/views";
import styles from "./InformationalPage.module.css";
import guide from "./ProjectGuide.module.css";

const navItems = ["Dashboard", "Scene Review", "How It Works", "About", "Data Sources", "Historical"];
const steps = [
  { title: "Set the time window", text: "Choose a preset or date range on the dashboard. The result contains matching records already imported; extending the range does not backfill missing history." },
  { title: "Compare like with like", text: "Keep the source and magnitude threshold consistent. Check timestamps and geographic coverage before comparing counts between dates or regions." },
  { title: "Read the record", text: "Inspect event details and original source context. Use regional activity shading for counts, while checking how many offshore records remain outside regional boundaries." },
];
type HistoricalBrowserProps = { onNavigate?: (view: View) => void; onSettings?: () => void };

export default function HistoricalBrowser({ onNavigate, onSettings }: HistoricalBrowserProps) {
  return <main className={styles.page}>
    <TopNav items={navItems} activeItem="Historical" theme="dashboard" onNavigate={onNavigate} onSettings={onSettings} />
    <div className={styles.content}>
      <header className={styles.intro}><p className={styles.eyebrow}>Records through time</p><h1 className={styles.title}>Historical Event Browser</h1><p className={styles.lead}>Start with the available records. Explore dates and sources today, with a clear view of what the collection includes.</p><div className={styles.actions}><a className={styles.action} href="/dashboard">Open live dashboard</a></div></header>
      <section className={guide.feature} aria-labelledby="available-title"><div><p className={guide.kicker}>Available now / Dashboard filters</p><h2 id="available-title">Look back.<br />Keep the context.</h2></div><div><p>The dashboard lets you filter imported earthquake records by date, source, and magnitude. This is the current route to exploring observations through time.</p><p>The dedicated historical comparison browser is a future feature. The links below open working dashboard filters, while a complete historical archive and side-by-side comparison tools remain planned.</p></div></section>
      <section aria-labelledby="catalog-title"><header className={guide.sectionHeader}><div><p className={styles.eyebrow}>01 / Choose a starting point</p><h2 id="catalog-title">Explore by source</h2></div><p>These views show the staging collection, not the provider’s entire historical catalog.</p></header>
        <div className={guide.grid}>
          <article className={guide.card}><span className={guide.tag}>Philippine earthquake reports</span><h3>PHIVOLCS observations</h3><p>Open the dashboard with PHIVOLCS selected, then adjust the date range and magnitude filter to review matching imported records.</p><div className={guide.cardLinks}><a className={guide.link} href="/dashboard?view=history&amp;source=phivolcs">Browse PHIVOLCS records</a></div></article>
          <article className={guide.card}><span className={guide.tag}>USGS earthquake observations</span><h3>USGS observations</h3><p>Open the same dashboard with USGS selected. Differences between source counts may reflect reporting coverage, selection criteria, or revisions.</p><div className={guide.cardLinks}><a className={guide.link} href="/dashboard?view=history&amp;source=usgs">Browse USGS records</a></div></article>
        </div>
      </section>
      <section aria-labelledby="compare-title"><header className={guide.sectionHeader}><div><p className={styles.eyebrow}>02 / A useful comparison</p><h2 id="compare-title">Three checks before counting</h2></div></header><ol className={`${guide.grid} ${guide.threeColumns} ${guide.steps}`}>{steps.map((step, index) => <li key={step.title} className={guide.card}><span className={guide.stepNumber}>0{index + 1}</span><h3>{step.title}</h3><p>{step.text}</p></li>)}</ol></section>
      <section className={guide.grid} aria-label="Archive scope">
        <article className={guide.card}><span className={guide.tag}>Need older observations?</span><h2>Go to the original catalog</h2><p>For dates outside the staging collection, start with the provider. Confirm the time zone, location bounds, and magnitude settings when comparing an official search with this dashboard.</p><div className={guide.cardLinks}><a className={guide.link} href="https://earthquake.usgs.gov/earthquakes/search/" target="_blank" rel="noopener noreferrer">Search the USGS catalog</a><a className={guide.link} href="https://earthquake.phivolcs.dost.gov.ph/" target="_blank" rel="noopener noreferrer">Visit PHIVOLCS bulletins</a></div></article>
        <article className={guide.card}><span className={guide.tag}>Planned / Dedicated archive</span><h2>A fuller comparison workspace</h2><p>A separate archive experience is intended to bring time-range comparisons and source-aware event context together. It is not currently a searchable archive on this page.</p><p>Offline research exports are separate inputs, not evidence that the staging collection contains every historical event.</p><div className={guide.cardLinks}><a className={guide.link} href="/data-sources">Understand source coverage</a></div></article>
      </section>
      <aside className={guide.note}><h2>A quiet record is not a safety assessment</h2><p>No matching observations can mean limited coverage or a restrictive filter. Recorded counts do not predict earthquakes, establish regional risk, or show that a location is safe.</p></aside>
      <footer className={guide.footer}><p>Explore observations with their dates, sources, and limitations.</p><div className={guide.footerLinks}><a className={guide.link} href="/">How It Works</a><a className={guide.link} href="/about">About the project</a></div></footer>
    </div>
  </main>;
}
