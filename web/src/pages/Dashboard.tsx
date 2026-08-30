import styles from "./Dashboard.module.css";
import DashboardMapArea from "../components/dashboard/DashboardMapArea";
import DashboardSidebar from "../components/dashboard/DashboardSidebar";
import TopNav from "../components/layout/TopNav";
import type { View } from "../types/views";
import { useEvents } from "../hooks/useEvents";

const navItems = [
  "Dashboard",
  "How It Works",
  "About",
  "Data Sources",
  "Contact",
];

type DashboardProps = {
  onNavigate?: (view: View) => void;
};

export default function Dashboard({ onNavigate }: DashboardProps) {
  const { data: events = [], isLoading, error, refetch } = useEvents();

  return (
    <div className={styles.page}>
      <TopNav
        items={navItems}
        activeItem="Dashboard"
        theme="dashboard"
        onNavigate={onNavigate}
      />

      <div className={styles.main}>
        <DashboardSidebar />
        <DashboardMapArea
          events={events}
          isLoading={isLoading}
          error={error as Error | null}
          onRetry={() => refetch()}
        />
      </div>
    </div>
  );
}
