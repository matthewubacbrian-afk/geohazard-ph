import TopNav from "../components/layout/TopNav";
import type { View } from "../types/views";
import jetPortrait from "../assets/team/jet-espanola.jpg";
import matthewPortrait from "../assets/team/matthew-ubac.jpg";
import johnPortrait from "../assets/team/john-dizon.jpg";
import styles from "./InformationalPage.module.css";
import about from "./About.module.css";

const navItems = ["Dashboard", "Scene Review", "How It Works", "About", "Data Sources", "Historical"];

const developers = [
  {
    id: "jet", name: "Jet Justine D. Española", role: "Lead Developer", portrait: jetPortrait,
    width: 720, height: 720,
    description: "Develops the backend and core system logic, shaping the architecture and application security.",
    contributions: ["Backend", "Architecture", "Security"],
  },
  {
    id: "matthew", name: "Matthew Brian P. Ubac", role: "Group Leader", portrait: matthewPortrait,
    width: 720, height: 720,
    description: "Leads the group and builds the data foundation, from database architecture to API integration and reliable connections.",
    contributions: ["Database design", "API integration", "Data architecture"],
  },
  {
    id: "john", name: "John Nathaniel B. Dizon", role: "Project Manager", portrait: johnPortrait,
    width: 720, height: 679,
    description: "Coordinates delivery and shapes the user experience, frontend workflows, and AI integration.",
    contributions: ["UI/UX", "Frontend", "AI integration"],
  },
];

const capabilities = [
  { step: "01 / Observe", title: "Follow recorded activity", text: "Explore earthquake observations and volcano bulletins with their sources and timestamps in view." },
  { step: "02 / Explore", title: "Put events in context", text: "Use maps, fault references, and regional activity summaries to understand where recorded events occur." },
  { step: "03 / Review", title: "Look closer at a scene", text: "Review visible objects and ground cues through on-device image analysis, with its limitations clearly explained." },
];

type AboutProps = {
  onNavigate?: (view: View) => void;
  onSettings?: () => void;
};

export default function About({ onNavigate, onSettings }: AboutProps) {
  return (
    <main className={styles.page}>
      <TopNav items={navItems} activeItem="About" theme="dashboard" onNavigate={onNavigate} onSettings={onSettings} />
      <div className={styles.content}>
        <header className={styles.intro}>
          <p className={styles.eyebrow}>The project &amp; the people</p>
          <h1 className={styles.title}>About GeoHazard PH</h1>
          <p className={styles.lead}>
            A clearer view of public hazard information, built for the Philippine context.
          </p>
          <div className={styles.actions}>
            <a className={styles.action} href="/dashboard">Explore the dashboard</a>
            <a className={about.teamLink} href="#developers">Meet the team <span aria-hidden="true">↘</span></a>
          </div>
        </header>

        <section className={about.mission} aria-labelledby="purpose-title">
          <div className={about.missionHeading}>
            <p className={about.missionEyebrow}>Why we are building this</p>
            <h2 id="purpose-title">Our purpose</h2>
            <span className={about.missionRule} aria-hidden="true" />
          </div>
          <div className={about.missionCopy}>
            <p className={about.missionLead}>Public observations.<br />A shared understanding.</p>
            <p>
              GeoHazard PH began with a simple idea: hazard information becomes more useful
              when people can explore it together, in one place. We bring recorded events,
              geographic references, and visual scene cues into a clear, accessible experience.
            </p>
            <p>
              Our goal is to support informed awareness and local planning for Philippine communities,
              local government units, and disaster-response teams, with visible sources and clear limits.
            </p>
          </div>
        </section>

        <div className={about.capabilities} aria-label="Project focus">
          {capabilities.map(({ step, title, text }) => <section key={step} className={about.capability}>
            <p className={styles.eyebrow}>{step}</p>
            <h2>{title}</h2>
            <p className={about.capabilityCopy}>{text}</p>
          </section>)}
        </div>

        <section id="developers" className={about.team} aria-labelledby="team-title">
          <header className={about.teamIntro}>
            <div>
              <p className={styles.eyebrow}>The people behind the project</p>
              <h2 id="team-title">Meet the developers</h2>
            </div>
            <p>Three complementary roles, working toward a clearer and more useful geohazard experience.</p>
          </header>
          <div className={about.teamGrid}>
            {developers.map((person) => <article key={person.id}
              className={`${about.member} ${person.id === "matthew" ? about.leader : ""}`}
              aria-labelledby={`${person.id}-name`}>
              <div className={about.portraitFrame}>
                <img src={person.portrait} alt={`Portrait of ${person.name}`}
                  width={person.width} height={person.height} loading="lazy" decoding="async" />
                <p className={about.role}>{person.role}</p>
              </div>
              <div className={about.memberCopy}>
                <h3 id={`${person.id}-name`}>{person.name}</h3>
                <p className={about.description}>{person.description}</p>
                <ul className={about.contributions} aria-label={`${person.name}'s contributions`}>
                  {person.contributions.map((contribution) => <li key={contribution}>{contribution}</li>)}
                </ul>
              </div>
            </article>)}
          </div>
        </section>

        <section className={about.limits} aria-labelledby="awareness-title">
          <h2 id="awareness-title">Built for awareness</h2>
          <div>
            <p>Recorded activity and visual scene cues are informational. They do not establish
              that an area is safe or predict future earthquakes. Follow official sources for emergency guidance.</p>
            <p className={about.advisory}>GeoHazard PH is not an official PHIVOLCS/NDRRMC advisory.</p>
          </div>
        </section>
      </div>
    </main>
  );
}
