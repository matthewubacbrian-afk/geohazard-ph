import TopNav from "../components/layout/TopNav";
import type { View } from "../types/views";
import styles from "./InformationalPage.module.css";
import guide from "./ProjectGuide.module.css";

const navItems = ["Dashboard", "Scene Review", "How It Works", "About", "Data Sources", "Historical"];
type DataSourcesProps = { onNavigate?: (view: View) => void; onSettings?: () => void };
const references = [
  { tag: "Static fault snapshot", title: "GEM active faults", text: "A selected snapshot from the Global Active Faults Database provides fault-line context. Coverage is not a complete site assessment.", credit: "GEM Global Active Faults Database / CC BY-SA 4.0", href: "https://github.com/GEMScienceTools/gem-global-active-faults", link: "View GEM fault dataset" },
  { tag: "Regional boundaries", title: "geoBoundaries", text: "Activity shading uses a pinned 17-region snapshot. Administrative boundaries can change; the display follows this recorded geometry rather than silently replacing it.", credit: "NAMRIA, PSA, OCHA Philippines via geoBoundaries / CC BY 3.0 IGO", href: "https://www.geoboundaries.org/", link: "Visit geoBoundaries" },
  { tag: "Optional coarse reference", title: "NASA landslide susceptibility", text: "A global susceptibility layer offers broad geographic context. Its coarse scale cannot identify the condition of an individual lot, road, or building.", credit: "Susceptibility is not a current landslide warning.", href: "https://gis.earthdata.nasa.gov/portal/home/item.html?id=d9c8e1279e3e48c2ab3dd318a6649b3a", link: "View NASA reference" },
];

export default function DataSources({ onNavigate, onSettings }: DataSourcesProps) {
  return <main className={styles.page}>
    <TopNav items={navItems} activeItem="Data Sources" theme="dashboard" onNavigate={onNavigate} onSettings={onSettings} />
    <div className={styles.content}>
      <header className={styles.intro}><p className={styles.eyebrow}>Provenance &amp; attribution</p><h1 className={styles.title}>Data Sources</h1><p className={styles.lead}>Know where an observation comes from, what a map layer represents, and how far the available information can take you.</p></header>
      <section className={guide.feature} aria-labelledby="provenance-title"><div><p className={guide.kicker}>The source stays in the story</p><h2 id="provenance-title">Traceable information.<br />Clearer interpretation.</h2></div><div><p>GeoHazard PH preserves provider names, timestamps, coordinates, and source context. Public observations, static map references, and research inputs serve different purposes.</p><p>Follow the original provider for revised reports, current bulletins, usage terms, and official guidance. Availability in this project does not imply provider endorsement.</p></div></section>
      <section aria-labelledby="observations-title"><header className={guide.sectionHeader}><div><p className={styles.eyebrow}>01 / Observations</p><h2 id="observations-title">Earthquakes &amp; bulletins</h2></div><p>Reporting catalogs can differ in coverage, timing, and later revisions.</p></header>
        <div className={guide.grid}>
          <article className={guide.card}><span className={guide.tag}>Earthquake feed</span><h3>USGS Earthquake Catalog</h3><p>Earthquake observations with event times, coordinates, magnitudes, and source identifiers. The staging import selects records relevant to the Philippine map area.</p><div className={guide.cardLinks}><a className={guide.link} href="https://earthquake.usgs.gov/earthquakes/search/" target="_blank" rel="noopener noreferrer">View USGS catalog</a></div></article>
          <article className={guide.card}><span className={guide.tag}>Philippine observations</span><h3>PHIVOLCS</h3><p>Philippine earthquake reports and volcano bulletin information. Imported summaries retain their source context; consult the original bulletin for the full statement and current status.</p><div className={guide.cardLinks}><a className={guide.link} href="https://earthquake.phivolcs.dost.gov.ph/" target="_blank" rel="noopener noreferrer">PHIVOLCS earthquake bulletins</a><a className={guide.link} href="https://wovodat.phivolcs.dost.gov.ph/bulletin/list-of-bulletin" target="_blank" rel="noopener noreferrer">Volcano bulletins</a></div></article>
        </div>
      </section>
      <section aria-labelledby="references-title"><header className={guide.sectionHeader}><div><p className={styles.eyebrow}>02 / Geographic context</p><h2 id="references-title">Map references</h2></div><p>Reference layers have their own scale and publication history. They do not update with every event.</p></header>
        <div className={`${guide.grid} ${guide.threeColumns}`}>{references.map((source) => <article className={guide.card} key={source.title}><span className={guide.tag}>{source.tag}</span><h3>{source.title}</h3><p>{source.text}</p><p>{source.credit}</p><div className={guide.cardLinks}><a className={guide.link} href={source.href} target="_blank" rel="noopener noreferrer">{source.link}</a></div></article>)}</div>
      </section>
      <section aria-labelledby="analysis-title"><header className={guide.sectionHeader}><div><p className={styles.eyebrow}>03 / Analysis &amp; research</p><h2 id="analysis-title">Different inputs, different limits</h2></div></header>
        <div className={guide.grid}>
          <article className={guide.card}><span className={guide.tag}>On-device scene analysis</span><h3>Public vision model</h3><p>The web experience downloads a pinned Xenova DETR ResNet-50 panoptic model and runs it locally. It recognizes general visual categories; it is not a validated geohazard detector.</p><p>Your selected image is not sent to an inference service.</p><div className={guide.cardLinks}><a className={guide.link} href="https://huggingface.co/Xenova/detr-resnet-50-panoptic/tree/ea24b2d4e0bfae31f0a1299ba3fb892a2df064de" target="_blank" rel="noopener noreferrer">View pinned model</a></div></article>
          <article className={guide.card}><span className={guide.tag}>Offline research inputs</span><h3>Historical seismic datasets</h3><p>Research experiments use historical PHIVOLCS and USGS dataset exports with recorded file provenance. These inputs are separate from the staging event feed and do not establish a complete dashboard archive.</p><p>Model-derived regional risk labels remain under review.</p><div className={guide.cardLinks}><a className={guide.link} href="https://github.com/matthewubacbrian-afk/geohazard-ph/blob/main/docs/data-sources.md" target="_blank" rel="noopener noreferrer">Read project source notes</a></div></article>
        </div>
      </section>
      <aside className={guide.note}><h2>Coverage is part of the context</h2><p>Missing reports do not mean no hazard. Counts reflect imported observations and selected filters; a source count is not proof of catalog completeness. Basemap credits remain visible on the map.</p><details className={guide.details}><summary>How to check an observation</summary><ul><li>Read its original source and event timestamp.</li><li>Compare the same date range, geographic coverage, and magnitude threshold.</li><li>Check for revised reports and consult official guidance before acting.</li></ul></details></aside>
      <footer className={guide.footer}><p>Source records may be revised by their providers.</p><div className={guide.footerLinks}><a className={guide.link} href="/">How It Works</a><a className={guide.link} href="/historical">Explore available records</a></div></footer>
    </div>
  </main>;
}
