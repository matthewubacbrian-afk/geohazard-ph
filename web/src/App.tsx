import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Hero from "./pages/Hero";
import About from "./pages/About";
import DataSources from "./pages/DataSources";
import HistoricalBrowser from "./pages/HistoricalBrowser";
import type { View } from "./types/views";
import SettingsPanel from "./components/common/SettingsPanel";

export default function App() {
  const [view, setView] = useState<View>("hero");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const onNavigate = (nextView: View) => setView(nextView);
  const pageProps = { onNavigate, onSettings: () => setSettingsOpen(true) };

  let page;
  switch (view) {
    case "dashboard":
      page = <Dashboard {...pageProps} />;
      break;
    case "about":
      page = <About {...pageProps} />;
      break;
    case "data-sources":
      page = <DataSources {...pageProps} />;
      break;
    case "historical":
      page = <HistoricalBrowser {...pageProps} />;
      break;
    case "hero":
    default:
      page = <Hero {...pageProps} />;
      break;
  }

  return <>{page}{settingsOpen && <SettingsPanel onClose={() => setSettingsOpen(false)} />}</>;
}
