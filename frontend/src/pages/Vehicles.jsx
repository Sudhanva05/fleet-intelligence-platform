
import { useEffect, useMemo, useState } from "react";
import { Search, RefreshCw, Truck, Activity, WifiOff } from "lucide-react";
import api, { getVehicleSummary } from "../services/api";

function Vehicles() {
  const [vehicles, setVehicles] = useState([]);
  const [summary, setSummary] = useState(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const fetchVehicles = async () => {
      try {
        const [fleetResponse, summaryResponse] = await Promise.all([
          api.get("/vehicles/"),
          getVehicleSummary(),
        ]);

        if (!cancelled) {
          setVehicles(fleetResponse.data.vehicles ?? []);
          setSummary(summaryResponse);
          setError("");
        }
      } catch (err) {
        console.error("Vehicle API error:", err);

        if (!cancelled) {
          setError("Unable to load vehicles. Check backend connection.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchVehicles();

    const interval = setInterval(fetchVehicles, 5000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const filteredVehicles = useMemo(() => {
    return vehicles.filter((vehicle) => {
      const matchesSearch = vehicle.vehicle_id
        ?.toLowerCase()
        .includes(search.toLowerCase());

      const matchesStatus =
        statusFilter === "all" || vehicle.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [vehicles, search, statusFilter]);

  return (
    <section className="dashboard-content vehicles-page">
      <div className="section-heading">
        <div>
          <h2>Vehicle Management</h2>
          <p>Manage and monitor all registered vehicles.</p>
        </div>
      </div>

      {error && <p className="error-message">{error}</p>}

      <div className="stats-grid">
        <div className="stat-card">
          <Truck />
          <h3>Total Vehicles</h3>
          <p>{loading ? "..." : summary?.total_vehicles ?? 0}</p>
        </div>

        <div className="stat-card">
          <Activity />
          <h3>Active Vehicles</h3>
          <p>{loading ? "..." : summary?.active_vehicles ?? 0}</p>
        </div>

        <div className="stat-card">
          <WifiOff />
          <h3>Stale Vehicles</h3>
          <p>{loading ? "..." : summary?.stale_vehicles ?? 0}</p>
        </div>
      </div>

      <div className="vehicle-toolbar">
        <div className="vehicle-search">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search by vehicle ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="all">All Statuses</option>
          <option value="active">Active</option>
          <option value="stale">Stale</option>
        </select>

        <button
          className="refresh-button"
          onClick={() => window.location.reload()}
          title="Refresh page"
        >
          <RefreshCw size={17} />
        </button>
      </div>

      <div className="vehicle-table-container">
        <table className="vehicle-table">
          <thead>
            <tr>
              <th>Vehicle ID</th>
              <th>Status</th>
              <th>Speed</th>
              <th>Fuel</th>
              <th>Latitude</th>
              <th>Longitude</th>
              <th>Last Updated</th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <tr>
                <td colSpan="7">Loading vehicles...</td>
              </tr>
            ) : filteredVehicles.length === 0 ? (
              <tr>
                <td colSpan="7">No vehicles found.</td>
              </tr>
            ) : (
              filteredVehicles.map((vehicle) => (
                <tr key={vehicle.vehicle_id}>
                  <td>{vehicle.vehicle_id.slice(0, 8)}</td>

                  <td>
                    <span className={`vehicle-status ${vehicle.status}`}>
                      {vehicle.status}
                    </span>
                  </td>

                  <td>{Number(vehicle.speed).toFixed(1)} km/h</td>
                  <td>{Number(vehicle.fuel_level).toFixed(1)}%</td>
                  <td>{Number(vehicle.latitude).toFixed(5)}</td>
                  <td>{Number(vehicle.longitude).toFixed(5)}</td>
                  <td>
                    {new Date(vehicle.timestamp).toLocaleString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <p className="vehicle-count">
        Showing {filteredVehicles.length} of {vehicles.length} vehicles
      </p>
    </section>
  );
}

export default Vehicles;
