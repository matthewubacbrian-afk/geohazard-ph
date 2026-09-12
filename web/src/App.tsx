import { useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Hero from "./pages/Hero";
import About from "./pages/About";
import DataSources from "./pages/DataSources";
import HistoricalBrowser from "./pages/HistoricalBrowser";
import type { View } from "./types/views";
import SettingsPanel from "./components/common/SettingsPanel";

const VIEW_PATHS: Record<View, string> = {
  hero: "/",
  dashboard: "/dashboard",
  about: "/about",
  "data-sources": "/data-sources",
  historical: "/historical",
};

function AppRoutes() {
  const navigate = useNavigate();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const onNavigate = (nextView: View) => {
    navigate(VIEW_PATHS[nextView]);
  };
  const pageProps = { onNavigate, onSettings: () => setSettingsOpen(true) };

  return (
    <>
      <Routes>
        <Route path="/" element={<Hero {...pageProps} />} />
        <Route path="/dashboard" element={<Dashboard {...pageProps} />} />
        <Route path="/about" element={<About {...pageProps} />} />
        <Route path="/data-sources" element={<DataSources {...pageProps} />} />
        <Route path="/historical" element={<HistoricalBrowser {...pageProps} />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      {settingsOpen && <SettingsPanel onClose={() => setSettingsOpen(false)} />}
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
