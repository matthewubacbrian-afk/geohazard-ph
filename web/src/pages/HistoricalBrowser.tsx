import ComingSoon from "../components/common/ComingSoon";
import TopNav from "../components/layout/TopNav";
import type { View } from "../types/views";

const navItems = ["Dashboard", "How It Works", "About", "Data Sources", "Contact"];

type HistoricalBrowserProps = {
  onNavigate?: (view: View) => void;
};

export default function HistoricalBrowser({ onNavigate }: HistoricalBrowserProps) {
  return (
    <main>
      <TopNav items={navItems} activeItem="Historical" onNavigate={onNavigate} />
      <ComingSoon
        title="Historical Event Browser"
        description="Search and explore past hazard events across the Philippines."
        note="Chronological records from USGS and PHIVOLCS."
      />
    </main>
  );
}
