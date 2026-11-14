
import { useEffect, useState } from "react";

import {
  Activity,
  Truck,
  Gauge,
  Fuel,
  AlertCircle,
} from "lucide-react";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

import api, { getFleetOverview } from "../services/api";

function Analytics() {
  const [overview, setOverview] = useState(null);
  const [speedTrend, setSpeedTrend] = useState([]);
  const [fuelTrend, setFuelTrend] = useState([]);

  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState("");

  const [vehicleAnalytics, setVehicleAnalytics] = useState(null);
  const [vehicleLoading, setVehicleLoading] = useState(false);
  const [vehicleError, setVehicleError] = useState("");

  const [vehicleHistory, setVehicleHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Fetch fleet-wide analytics
  useEffect(() => {
    let cancelled = false;

    const fetchAnalytics = async () => {
      try {
        const [
          overviewData,
          speedResponse,
          fuelResponse,
          vehiclesResponse,
        ] = await Promise.all([
          getFleetOverview(),
          api.get("/analytics/speed"),
          api.get("/analytics/fuel"),
          api.get("/analytics/vehicles"),
        ]);

        if (!cancelled) {
          setOverview(overviewData);

          setSpeedTrend(
            speedResponse.data.speed_trend ?? []
          );

          setFuelTrend(
            fuelResponse.data.fuel_trend ?? []
          );

          setVehicles(
            vehiclesResponse.data.vehicles ?? []
          );

          setError("");
        }
      } catch (err) {
        console.error("Analytics API error:", err);

        if (!cancelled) {
          setError(
            "Unable to load analytics. Check backend connection."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchAnalytics();

    return () => {
      cancelled = true;
    };
  }, []);

  // Fetch selected vehicle analytics
  useEffect(() => {
    if (!selectedVehicle) {
      setVehicleAnalytics(null);
      setVehicleError("");
      setVehicleLoading(false);
      return;
    }

    let cancelled = false;

    const fetchVehicleAnalytics = async () => {
      setVehicleLoading(true);
      setVehicleAnalytics(null);
      setVehicleError("");

      try {
        const response = await api.get(
          `/analytics/vehicle/${selectedVehicle}`
        );

        if (!cancelled) {
          setVehicleAnalytics(response.data.analytics);
        }
      } catch (err) {
        console.error("Vehicle analytics error:", err);

        if (!cancelled) {
          setVehicleError(
            "Unable to load analytics for this vehicle."
          );
        }
      } finally {
        if (!cancelled) {
          setVehicleLoading(false);
        }
      }
    };

    fetchVehicleAnalytics();

    return () => {
      cancelled = true;
    };
  }, [selectedVehicle]);

  // Fetch selected vehicle history
  useEffect(() => {
    if (!selectedVehicle) {
      setVehicleHistory([]);
      setHistoryError("");
      setHistoryLoading(false);
      return;
    }

    let cancelled = false;

    const fetchVehicleHistory = async () => {
      setHistoryLoading(true);
      setVehicleHistory([]);
      setHistoryError("");

      try {
        const response = await api.get(
          `/analytics/vehicle/${selectedVehicle}/history`
        );

        if (!cancelled) {
          const records =
            response.data.history ?? response.data;

          const formattedRecords = records.map((record) => ({
            time: record.timestamp,
            speed: record.speed,
            fuel: record.fuel_level,
          }));

          setVehicleHistory(formattedRecords);
        }
      } catch (err) {
        console.error("Vehicle history error:", err);

        if (!cancelled) {
          setHistoryError(
            "Unable to load historical data for this vehicle."
          );
        }
      } finally {
        if (!cancelled) {
          setHistoryLoading(false);
        }
      }
    };

    fetchVehicleHistory();

    return () => {
      cancelled = true;
    };
  }, [selectedVehicle]);

  // Format chart time
  const formatTime = (value) => {
    if (!value) return "";

    const date = new Date(value.replace(" ", "T"));

    return `${String(date.getMonth() + 1).padStart(2, "0")}-${String(
      date.getDate()
    ).padStart(2, "0")} ${String(date.getHours()).padStart(2, "0")}:${String(
      date.getMinutes()
    ).padStart(2, "0")}`;
  };

  // Format full timestamp for tooltips
  const formatFullTime = (value) => {
    if (!value) return "";
    return String(value).replace("T", " ");
  };

  // Format tooltip values with units
  const formatTooltipValue = (value, name) => {
    const unit = name === "Speed" ? "km/h" : "%";

    return [
      `${Number(value).toFixed(2)} ${unit}`,
      name,
    ];
  };

  // Choose chart data based on selection
  const chartSpeedData = selectedVehicle
    ? vehicleHistory
    : speedTrend;

  const chartFuelData = selectedVehicle
    ? vehicleHistory
    : fuelTrend;

  const speedDataKey = selectedVehicle
    ? "speed"
    : "average_speed";

  const fuelDataKey = selectedVehicle
    ? "fuel"
    : "average_fuel";

  // Fleet-wide KPI cards
  const statCards = [
    {
      title: "Total Events",
      value: overview?.total_events?.toLocaleString() ?? 0,
      icon: Activity,
    },
    {
      title: "Total Vehicles",
      value: overview?.total_vehicles?.toLocaleString() ?? 0,
      icon: Truck,
    },
    {
      title: "Average Speed",
      value: overview?.average_speed ?? 0,
      unit: "km/h",
      icon: Gauge,
    },
    {
      title: "Average Fuel",
      value: overview?.average_fuel ?? 0,
      unit: "%",
      icon: Fuel,
    },
  ];

  // Selected vehicle KPI cards
  const vehicleStatCards = vehicleAnalytics
    ? [
        {
          title: "Total Events",
          value:
            vehicleAnalytics.total_events?.toLocaleString() ?? 0,
          icon: Activity,
        },
        {
          title: "Average Speed",
          value: vehicleAnalytics.average_speed ?? 0,
          unit: "km/h",
          icon: Gauge,
        },
        {
          title: "Minimum Speed",
          value: vehicleAnalytics.minimum_speed ?? 0,
          unit: "km/h",
          icon: Gauge,
        },
        {
          title: "Maximum Speed",
          value: vehicleAnalytics.maximum_speed ?? 0,
          unit: "km/h",
          icon: Gauge,
        },
        {
          title: "Average Fuel",
          value: vehicleAnalytics.average_fuel ?? 0,
          unit: "%",
          icon: Fuel,
        },
      ]
    : [];

  return (
    <section className="dashboard-content analytics-page">

      {/* Section Heading and Vehicle Filter */}
      <div className="section-heading analytics-heading">
        <div>
          <h2>Fleet Analytics</h2>
          <p>
            Historical performance and telemetry insights.
          </p>
        </div>

        <div className="vehicle-filter">
          <label htmlFor="vehicle-select">
            Analyze Vehicle
          </label>

          <select
            id="vehicle-select"
            value={selectedVehicle}
            onChange={(e) =>
              setSelectedVehicle(e.target.value)
            }
          >
            <option value="">Fleet Overview</option>

            {vehicles.map((vehicle) => (
              <option key={vehicle} value={vehicle}>
                {vehicle}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Fleet Error */}
      {error && (
        <div className="error-message">
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      {/* Fleet-wide KPI Cards */}
      <div className="stats-grid analytics-stats">
        {statCards.map((card) => {
          const Icon = card.icon;

          return (
            <div className="stat-card" key={card.title}>
              <Icon />
              <h3>{card.title}</h3>

              <p>
                {loading ? "..." : card.value}
                {card.unit && !loading
                  ? ` ${card.unit}`
                  : ""}
              </p>
            </div>
          );
        })}
      </div>

      {/* Selected Vehicle Analytics */}
      {selectedVehicle && (
        <div className="vehicle-analytics-panel">

          <div className="vehicle-analytics-heading">
            <div>
              <h3>Vehicle Performance</h3>
              <p>{selectedVehicle}</p>
            </div>
          </div>

          {vehicleLoading && (
            <p>Loading vehicle analytics...</p>
          )}

          {vehicleError && (
            <div className="error-message">
              <AlertCircle size={18} />
              {vehicleError}
            </div>
          )}

          {vehicleAnalytics && !vehicleLoading && (
            <div className="stats-grid analytics-stats">
              {vehicleStatCards.map((card) => {
                const Icon = card.icon;

                return (
                  <div
                    className="stat-card"
                    key={card.title}
                  >
                    <Icon />
                    <h3>{card.title}</h3>

                    <p>
                      {card.value}
                      {card.unit ? ` ${card.unit}` : ""}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Analytics Charts */}
      <div className="analytics-charts">

        {/* Speed Chart */}
        <div className="analytics-chart-card">

          <h3>
            {selectedVehicle
              ? "Vehicle Speed History"
              : "Average Fleet Speed"}
          </h3>

          <p>
            {selectedVehicle
              ? "Historical speed for selected vehicle"
              : "Speed trend grouped by minute"}
          </p>

          <div className="chart-container">
            {loading || (selectedVehicle && historyLoading) ? (
              <p>Loading speed data...</p>
            ) : selectedVehicle && historyError ? (
              <p>{historyError}</p>
            ) : chartSpeedData.length === 0 ? (
              <p>No speed data available.</p>
            ) : (
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <LineChart data={chartSpeedData}>
                  <CartesianGrid
                    stroke="#263244"
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="time"
                    tickFormatter={formatTime}
                    stroke="#94a3b8"
                    minTickGap={35}
                    interval="preserveStartEnd"
                  />

                  <YAxis stroke="#94a3b8" />

                  <Tooltip
                    labelFormatter={(label) =>
                      `Timestamp: ${formatFullTime(label)}`
                    }
                    formatter={formatTooltipValue}
                    contentStyle={{
                      backgroundColor: "#111827",
                      border: "1px solid #263244",
                      borderRadius: "8px",
                      color: "#fff",
                    }}
                    labelStyle={{
                      color: "#38bdf8",
                      marginBottom: "6px",
                    }}
                  />

                  <Line
                    type="monotone"
                    dataKey={speedDataKey}
                    name="Speed"
                    stroke="#38bdf8"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Fuel Chart */}
        <div className="analytics-chart-card">

          <h3>
            {selectedVehicle
              ? "Vehicle Fuel History"
              : "Average Fuel Level"}
          </h3>

          <p>
            {selectedVehicle
              ? "Historical fuel level for selected vehicle"
              : "Fuel trend grouped by minute"}
          </p>

          <div className="chart-container">
            {loading || (selectedVehicle && historyLoading) ? (
              <p>Loading fuel data...</p>
            ) : selectedVehicle && historyError ? (
              <p>{historyError}</p>
            ) : chartFuelData.length === 0 ? (
              <p>No fuel data available.</p>
            ) : (
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <LineChart data={chartFuelData}>
                  <CartesianGrid
                    stroke="#263244"
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="time"
                    tickFormatter={formatTime}
                    stroke="#94a3b8"
                    minTickGap={35}
                    interval="preserveStartEnd"
                  />

                  <YAxis stroke="#94a3b8" />

                  <Tooltip
                    labelFormatter={(label) =>
                      `Timestamp: ${formatFullTime(label)}`
                    }
                    formatter={formatTooltipValue}
                    contentStyle={{
                      backgroundColor: "#111827",
                      border: "1px solid #263244",
                      borderRadius: "8px",
                      color: "#fff",
                    }}
                    labelStyle={{
                      color: "#34d399",
                      marginBottom: "6px",
                    }}
                  />

                  <Line
                    type="monotone"
                    dataKey={fuelDataKey}
                    name="Fuel Level"
                    stroke="#34d399"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

      </div>
    </section>
  );
}

export default Analytics;
