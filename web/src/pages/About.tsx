import ComingSoon from "../components/common/ComingSoon";
import TopNav from "../components/layout/TopNav";
import type { View } from "../types/views";

const navItems = ["Dashboard", "How It Works", "About", "Data Sources", "Contact"];

type AboutProps = {
  onNavigate?: (view: View) => void;
  onSettings?: () => void;
};

export default function About({ onNavigate, onSettings }: AboutProps) {
  return (
    <main>
      <TopNav items={navItems} activeItem="About" onNavigate={onNavigate} onSettings={onSettings} />
      <ComingSoon
        title="About GeoHazard"
        description="GeoHazard bridges complex geophysical data and pragmatic local governance for Philippine LGUs and disaster-response offices."
        note="Data sources: USGS, PHIVOLCS, Smithsonian GVP, GEM."
      />
    </main>
  );
}
