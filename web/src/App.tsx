import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Hero from "./pages/Hero";

export default function App() {
  const [view, setView] = useState<"hero" | "dashboard">("hero");

  if (view === "dashboard") {
    return <Dashboard />;
  }

  return <Hero onNavigate={(nextView) => setView(nextView)} />;
}
