
import { useEffect, useMemo, useState } from "react";
import {
  Search,
  RefreshCw,
  Truck,
  Activity,
  WifiOff,
  X,
  MapPin,
  Clock,
  Gauge,
  Fuel,
  Play,
  Pause,
  AlertTriangle,
} from "lucide-react";

import api, { getVehicleSummary } from "../services/api";

const LOW_FUEL_THRESHOLD = 20;

function getOperationalStatus(vehicle) {
  if (vehicle.status !== "active") {
    return "inactive";
  }

  const speed = Number(vehicle.speed) || 0;

  if (speed >= 20) return "moving";
  if (speed > 0) return "slow";
  return "idle";
}

function Vehicles() {
  const [vehicles, setVehicles] = useState([]);
  const [summary, setSummary] = useState(null);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
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
          setRefreshing(false);
        }
      }
    };

    fetchVehicles();

    const interval = setInterval(fetchVehicles, 5000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [refreshKey]);

  const filteredVehicles = useMemo(() => {
    return vehicles.filter((vehicle) => {
      const vehicleId = vehicle.vehicle_id?.toLowerCase() ?? "";
      const matchesSearch = vehicleId.includes(search.toLowerCase());

      const operationalStatus = getOperationalStatus(vehicle);
      const fuelLevel = Number(vehicle.fuel_level) || 0;

      let matchesStatus = true;

      if (statusFilter === "active" || statusFilter === "stale") {
        matchesStatus = vehicle.status === statusFilter;
      } else if (
        ["moving", "slow", "idle", "inactive"].includes(statusFilter)
      ) {
        matchesStatus = operationalStatus === statusFilter;
      } else if (statusFilter === "low-fuel") {
        matchesStatus = fuelLevel <= LOW_FUEL_THRESHOLD;
      }

      return matchesSearch && matchesStatus;
    });
  }, [vehicles, search, statusFilter]);

  const handleRefresh = () => {
    setRefreshing(true);
    setRefreshKey((previous) => previous + 1);
  };

  const selectedOperationalStatus = selectedVehicle
    ? getOperationalStatus(selectedVehicle)
    : "";

  return (
    <section className="dashboard-content vehicles-page">
      <div className="section-heading">
        <div>
          <h2>Vehicle Management</h2>
          <p>Manage and monitor all registered vehicles.</p>
        </div>
      </div>

      {error && <p className="error-message">{error}</p>}

      {/* Fleet Summary */}
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

      {/* Search and Filters */}
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
          <option value="all">All Vehicles</option>
          <option value="active">Active</option>
          <option value="stale">Stale</option>
          <option value="moving">Moving</option>
          <option value="slow">Slow Moving</option>
          <option value="idle">Idle</option>
          <option value="inactive">Inactive</option>
          <option value="low-fuel">Low Fuel</option>
        </select>

        <button
          className="refresh-button"
          onClick={handleRefresh}
          disabled={refreshing}
          title="Refresh vehicles"
        >
          <RefreshCw
            size={17}
            className={refreshing ? "spinning" : ""}
          />
        </button>
      </div>

      {/* Vehicle Table */}
      <div className="vehicle-table-container">
        <table className="vehicle-table">
          <thead>
            <tr>
              <th>Vehicle ID</th>
              <th>Connection</th>
              <th>Operational Status</th>
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
                <td colSpan="8">Loading vehicles...</td>
              </tr>
            ) : filteredVehicles.length === 0 ? (
              <tr>
                <td colSpan="8">No vehicles found.</td>
              </tr>
            ) : (
              filteredVehicles.map((vehicle) => {
                const operationalStatus = getOperationalStatus(vehicle);
                const fuelLevel = Number(vehicle.fuel_level) || 0;
                const lowFuel = fuelLevel <= LOW_FUEL_THRESHOLD;

                return (
                  <tr
                    key={vehicle.vehicle_id}
                    onClick={() => setSelectedVehicle(vehicle)}
                    className="clickable-vehicle-row"
                  >
                    <td>{vehicle.vehicle_id.slice(0, 8)}</td>

                    <td>
                      <span className={`vehicle-status ${vehicle.status}`}>
                        {vehicle.status}
                      </span>
                    </td>

                    <td>
                      <span
                        className={`vehicle-operational-status ${operationalStatus}`}
                      >
                        {operationalStatus}
                      </span>
                    </td>

                    <td>
                      {(Number(vehicle.speed) || 0).toFixed(1)} km/h
                    </td>

                    <td>
                      <span className={lowFuel ? "fuel-warning" : ""}>
                        {fuelLevel.toFixed(1)}%
                      </span>
                      {lowFuel && (
                        <span className="low-fuel-label">
                          Low fuel
                        </span>
                      )}
                    </td>

                    <td>{Number(vehicle.latitude).toFixed(5)}</td>
                    <td>{Number(vehicle.longitude).toFixed(5)}</td>

                    <td>
                      {new Date(vehicle.timestamp).toLocaleString()}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <p className="vehicle-count">
        Showing {filteredVehicles.length} of {vehicles.length} vehicles
      </p>

      {/* Vehicle Details Panel */}
      {selectedVehicle && (
        <div
          className="vehicle-details-overlay"
          onClick={() => setSelectedVehicle(null)}
        >
          <aside
            className="vehicle-details-panel"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="vehicle-details-header">
              <div>
                <h2>Vehicle Details</h2>
                <p>Complete vehicle information</p>
              </div>

              <button
                className="close-panel-button"
                onClick={() => setSelectedVehicle(null)}
                aria-label="Close vehicle details"
              >
                <X size={20} />
              </button>
            </div>

            <div className="vehicle-identity">
              <div className="vehicle-icon">
                <Truck size={28} />
              </div>

              <div>
                <h3>{selectedVehicle.vehicle_id.slice(0, 8)}</h3>

                <span
                  className={`vehicle-status ${selectedVehicle.status}`}
                >
                  {selectedVehicle.status}
                </span>
              </div>
            </div>

            <div className="vehicle-detail-grid">
              <div className="vehicle-detail-card">
                <Gauge size={20} />
                <span>Current Speed</span>
                <strong>
                  {(Number(selectedVehicle.speed) || 0).toFixed(1)} km/h
                </strong>
              </div>

              <div className="vehicle-detail-card">
                <Fuel size={20} />
                <span>Fuel Level</span>
                <strong>
                  {(Number(selectedVehicle.fuel_level) || 0).toFixed(1)}%
                </strong>
              </div>
            </div>

            <div className="vehicle-detail-section">
              <h4>
                <Activity size={18} /> Operational Information
              </h4>

              <div className="vehicle-detail-row">
                <span>Operational Status</span>
                <strong
                  className={`vehicle-operational-text ${selectedOperationalStatus}`}
                >
                  {selectedOperationalStatus}
                </strong>
              </div>

              <div className="vehicle-detail-row">
                <span>Fuel Condition</span>
                <strong
                  className={
                    Number(selectedVehicle.fuel_level) <= LOW_FUEL_THRESHOLD
                      ? "fuel-warning"
                      : ""
                  }
                >
                  {Number(selectedVehicle.fuel_level).toFixed(1) <=
                  LOW_FUEL_THRESHOLD
                    ? "Low Fuel"
                    : "Normal"}
                </strong>
              </div>
            </div>

            <div className="vehicle-detail-section">
              <h4>
                <MapPin size={18} /> Location Information
              </h4>

              <div className="vehicle-detail-row">
                <span>Latitude</span>
                <strong>
                  {Number(selectedVehicle.latitude).toFixed(6)}
                </strong>
              </div>

              <div className="vehicle-detail-row">
                <span>Longitude</span>
                <strong>
                  {Number(selectedVehicle.longitude).toFixed(6)}
                </strong>
              </div>
            </div>

            <div className="vehicle-detail-section">
              <h4>
                <Clock size={18} /> Telemetry Information
              </h4>

              <div className="vehicle-detail-row">
                <span>Last Updated</span>
                <strong>
                  {new Date(selectedVehicle.timestamp).toLocaleString()}
                </strong>
              </div>

              <div className="vehicle-detail-row">
                <span>Full Vehicle ID</span>
                <strong className="full-vehicle-id">
                  {selectedVehicle.vehicle_id}
                </strong>
              </div>
            </div>
          </aside>
        </div>
      )}
    </section>
  );
}

export default Vehicles;
