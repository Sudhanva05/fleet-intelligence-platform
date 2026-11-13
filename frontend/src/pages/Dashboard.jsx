
import { useEffect, useState } from "react";
import { Truck, Activity, Gauge, Fuel } from "lucide-react";

import StatCard from "../components/StatCard";
import FleetMap from "../components/FleetMap";

import {
  getVehicleSummary,
  getFleetOverview,
} from "../services/api";

import api from "../services/api";

function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [overview, setOverview] = useState(null);
  const [vehicles, setVehicles] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [vehicleData, analyticsData, fleetData] =
          await Promise.all([
            getVehicleSummary(),
            getFleetOverview(),
            api.get("/vehicles/"),
          ]);

        setSummary(vehicleData);
        setOverview(analyticsData);
        setVehicles(fleetData.data.vehicles);
        setError("");
      } catch (err) {
        console.error("Dashboard API error:", err);
        setError("Unable to load fleet data. Check backend connection.");
      }
    };

    fetchDashboardData();

    const interval = setInterval(fetchDashboardData, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <section className="dashboard-content">
      <div className="section-heading">
        <div>
          <h2>Fleet Overview</h2>
          <p>Real-time fleet performance and historical analytics</p>
        </div>
      </div>

      {error && <p className="error-message">{error}</p>}

      <div className="stats-grid">
        <StatCard
          title="Total Vehicles"
          value={summary?.total_vehicles}
          icon={Truck}
          color="blue"
        />

        <StatCard
          title="Active Vehicles"
          value={summary?.active_vehicles}
          icon={Activity}
          color="green"
        />

        <StatCard
          title="Average Speed"
          value={overview?.average_speed}
          unit=" km/h"
          icon={Gauge}
          color="orange"
        />

        <StatCard
          title="Average Fuel"
          value={overview?.average_fuel}
          unit="%"
          icon={Fuel}
          color="purple"
        />
      </div>

      <div className="map-section">
        <div className="section-heading">
          <div>
            <h2>Live Fleet Tracking</h2>
            <p>
              Monitoring {vehicles.length} stored vehicle locations
            </p>
          </div>
        </div>

        <FleetMap vehicles={vehicles} />
      </div>
    </section>
  );
}

export default Dashboard;
