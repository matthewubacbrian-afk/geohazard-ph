import styles from "./TopNav.module.css";

type TopNavProps = {
  items: string[];
  activeItem?: string;
  onNavigate?: (view: "dashboard") => void;
  theme?: "hero" | "dashboard";
};

export default function TopNav({
  items,
  activeItem,
  onNavigate,
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

          return (
            <li key={item}>
              {item === "Dashboard" && onNavigate ? (
                <button
                  type="button"
                  className={linkClassName}
                  onClick={() => onNavigate("dashboard")}
                >
                  {item}
                </button>
              ) : (
                <a href="#" className={linkClassName} aria-current={isActive ? "page" : undefined}>
                  {item}
                </a>
              )}
            </li>
          );
        })}
      </ul>

      <button type="button" className={styles.settingsBtn}>
        Settings
      </button>
    </nav>
  );
}
