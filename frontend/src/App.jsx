
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import "./App.css";

function App() {
  return (
    <div className="app-layout">
      <Sidebar />

      <main className="main-content">
        <header className="topbar">
          <div>
            <h1>Fleet Dashboard</h1>
            <p>Monitor and manage your fleet in real time.</p>
          </div>

          <div className="system-status">
            <span className="status-dot"></span>
            System Operational
          </div>
        </header>

        <Dashboard />
      </main>
    </div>
  );
}

export default App;
