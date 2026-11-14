
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";

import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Vehicles from "./pages/Vehicles";

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
