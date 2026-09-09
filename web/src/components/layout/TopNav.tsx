import type { View } from "../../types/views";
import styles from "./TopNav.module.css";

type TopNavProps = {
  items: string[];
  activeItem?: string;
  onNavigate?: (view: View) => void;
  onSettings?: () => void;
  theme?: "hero" | "dashboard";
};

// Map a nav label to an app view, for items that navigate. Labels without a
// mapping render as placeholder links.
const NAV_VIEWS: Record<string, View> = {
  Dashboard: "dashboard",
  "How It Works": "hero",
  About: "about",
  "Data Sources": "data-sources",
  Historical: "historical",
};

export default function TopNav({
  items,
  activeItem,
  onNavigate,
  onSettings,
  theme = "hero",
}: TopNavProps) {
  const isDashboardTheme = theme === "dashboard";
  const resolvedActiveItem =
    activeItem ?? (isDashboardTheme ? "Dashboard" : "How It Works");

  return (
    <nav
      className={`${styles.nav} ${isDashboardTheme ? styles["nav--dashboard"] : ""}`}
      aria-label="Main navigation"
    >
      <div className={styles.brand}>GeoHazard</div>

      <ul className={styles.links}>
        {items.map((item) => {
          const isActive = item === resolvedActiveItem;
          const linkClassName = `${styles.linkBtn} ${
            isActive ? styles.linkBtnActive : ""
          }`;
          const targetView = NAV_VIEWS[item];

          return (
            <li key={item}>
              {targetView && onNavigate ? (
                <button
                  type="button"
                  className={linkClassName}
                  aria-current={isActive ? "page" : undefined}
                  onClick={() => onNavigate(targetView)}
                >
                  {item}
                </button>
              ) : (
                <a
                  href={item === "Contact" ? "mailto:support@geohazard.ph" : "#"}
                  className={linkClassName}
                  aria-current={isActive ? "page" : undefined}
                  onClick={item === "Contact" ? undefined : (event) => event.preventDefault()}
                >
                  {item}
                </a>
              )}
            </li>
          );
        })}
      </ul>

      <button type="button" className={styles.settingsBtn} onClick={onSettings}>
        Settings
      </button>
    </nav>
  );
}
