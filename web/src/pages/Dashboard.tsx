import DashboardMapArea from "../components/dashboard/DashboardMapArea";
import DashboardSidebar from "../components/dashboard/DashboardSidebar";
import TopNav from "../components/layout/TopNav";

const navItems = [
  "Dashboard",
  "How It Works",
  "About",
  "Data Sources",
  "Contact",
];

export default function Dashboard() {
  return (
    <div className="dashboard-page">
      <TopNav items={navItems} activeItem="Dashboard" theme="dashboard" />

      <div className="dashboard-main">
        <DashboardSidebar />
        <DashboardMapArea />
      </div>
    </div>
  );
}
