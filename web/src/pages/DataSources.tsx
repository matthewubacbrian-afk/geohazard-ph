import ComingSoon from "../components/common/ComingSoon";
import TopNav from "../components/layout/TopNav";
import type { View } from "../types/views";

const navItems = ["Dashboard", "How It Works", "About", "Data Sources", "Contact"];

type DataSourcesProps = {
  onNavigate?: (view: View) => void;
};

export default function DataSources({ onNavigate }: DataSourcesProps) {
  return (
    <main>
      <TopNav items={navItems} activeItem="Data Sources" onNavigate={onNavigate} />
      <ComingSoon
        title="Data Sources"
        description="Seismic and geologic records aggregated from trusted public sources."
        note="USGS · PHIVOLCS · Smithsonian GVP · GEM."
      />
    </main>
  );
}
