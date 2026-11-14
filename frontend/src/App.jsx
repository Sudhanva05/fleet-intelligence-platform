
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import LiveTracking from "./pages/LiveTracking";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Vehicles from "./pages/Vehicles";
import Analytics from "./pages/Analytics";

import "./App.css";

function AppLayout() {
  const location = useLocation();

  const pageInfo = {
    "/": {
      title: "Fleet Dashboard",
      subtitle: "Monitor and manage your fleet in real time.",
    },
    "/vehicles": {
      title: "Vehicle Management",
      subtitle: "Search, monitor and manage your fleet vehicles.",
    },
    "/tracking": {
      title: "Live Fleet Tracking",
      subtitle: "Monitor vehicle locations in real time.",
    },
    "/analytics": {
      title: "Fleet Analytics",
      subtitle: "Historical performance and telemetry insights.",
    },
  };

  const currentPage = pageInfo[location.pathname] || pageInfo["/"];

  return (
    <div className="app-layout">
      <Sidebar />

      <main className="main-content">
        <header className="topbar">
          <div>
            <h1>{currentPage.title}</h1>
            <p>{currentPage.subtitle}</p>
          </div>

          <div className="system-status">
            <span className="status-dot"></span>
            System Operational
          </div>
        </header>

        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/vehicles" element={<Vehicles />} />
          <Route path="*" element={<Navigate to="/" replace />} />
          <Route path="/tracking" element={<LiveTracking />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}

export default App;
