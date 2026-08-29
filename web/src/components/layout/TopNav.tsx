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
      className={isDashboardTheme ? "dashboard-topbar" : "top-nav"}
      aria-label="Main navigation"
    >
      <div className={isDashboardTheme ? "dashboard-brand" : "nav-logo"}>
        GeoHazard
      </div>

      <ul className={isDashboardTheme ? "dashboard-nav" : "nav-links"}>
        {items.map((item) => {
          const isDashboardItem = item === "Dashboard";
          const isActive = item === resolvedActiveItem;
          const linkClassName = isDashboardTheme
            ? `dashboard-nav-link ${isActive ? "dashboard-nav-link--active" : ""}`
            : `nav-link ${isActive ? "nav-link--active" : ""}`;

          return (
            <li
              key={item}
              className={isDashboardTheme ? "dashboard-nav-item" : ""}
            >
              {isDashboardItem && onNavigate ? (
                <button
                  type="button"
                  className={linkClassName}
                  onClick={() => onNavigate("dashboard")}
                >
                  {item}
                </button>
              ) : (
                <a href="#" className={linkClassName}>
                  {item}
                </a>
              )}
            </li>
          );
        })}
      </ul>

      <button
        type="button"
        className={isDashboardTheme ? "dashboard-lang-button" : "lang-button"}
      >
        Settings
      </button>
    </nav>
  );
}
