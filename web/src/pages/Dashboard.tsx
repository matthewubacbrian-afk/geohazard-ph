import DashboardMapArea from "../components/dashboard/DashboardMapArea";
import DashboardSidebar from "../components/dashboard/DashboardSidebar";
import TopNav from "../components/layout/TopNav";
import { useEvents } from "../hooks/useEvents";

const navItems = [
  "Dashboard",
  "How It Works",
  "About",
  "Data Sources",
  "Contact",
];

export default function Dashboard() {
  const { data: events = [] } = useEvents();

  return (
    <div className="dashboard-page">
      <TopNav items={navItems} activeItem="Dashboard" theme="dashboard" />

      <div className="dashboard-main">
        <DashboardSidebar />
        <DashboardMapArea events={events} />
      </div>
    </div>
  );
}
