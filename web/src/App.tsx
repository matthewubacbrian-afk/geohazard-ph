import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Hero from "./pages/Hero";
import About from "./pages/About";
import DataSources from "./pages/DataSources";
import type { View } from "./types/views";

export default function App() {
  const [view, setView] = useState<View>("hero");
  const onNavigate = (nextView: View) => setView(nextView);

  switch (view) {
    case "dashboard":
      return <Dashboard onNavigate={onNavigate} />;
    case "about":
      return <About onNavigate={onNavigate} />;
    case "data-sources":
      return <DataSources onNavigate={onNavigate} />;
    case "hero":
    default:
      return <Hero onNavigate={onNavigate} />;
  }
}
