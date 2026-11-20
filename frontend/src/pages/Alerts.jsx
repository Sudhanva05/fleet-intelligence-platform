
import { useCallback, useEffect, useState } from "react";

import {
  AlertTriangle,
  BellRing,
  Clock,
  RefreshCw,
  Search,
  ShieldAlert,
  Fuel,
  Gauge,
  CircleCheck,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

import {
  getActiveAlerts,
  getAlertSummary,
  getAlertHistory,
} from "../services/api";


const PAGE_SIZE = 10;


function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleString();
}


function formatValue(alert) {
  if (alert.current_value == null) return "—";

  const value = Number(alert.current_value);

  if (!Number.isFinite(value)) return "—";

  if (alert.alert_type === "LOW_FUEL") {
    return `${value.toFixed(1)}%`;
  }

  if (alert.alert_type === "OVERSPEED") {
    return `${value.toFixed(1)} km/h`;
  }

  if (alert.alert_type === "PROLONGED_IDLE") {
    return `${Math.floor(value)} sec`;
  }

  if (alert.alert_type === "INACTIVE") {
    return `${Math.floor(value)} sec`;
  }

  return value.toFixed(1);
}


function getAlertIcon(alertType) {
  switch (alertType) {
    case "LOW_FUEL":
      return Fuel;

    case "OVERSPEED":
      return Gauge;

    case "INACTIVE":
      return Clock;

    case "PROLONGED_IDLE":
      return AlertTriangle;

    default:
      return BellRing;
  }
}


function getAlertLabel(alertType) {
  const labels = {
    LOW_FUEL: "Low Fuel",
    OVERSPEED: "Overspeed",
    INACTIVE: "Inactive Vehicle",
    PROLONGED_IDLE: "Prolonged Idle",
  };

  return labels[alertType] || alertType?.replaceAll("_", " ") || "Unknown";
}


function SeverityBadge({ severity }) {
  const value = severity?.toLowerCase() || "unknown";

  return (
    <span className={`alert-badge severity-${value}`}>
      {severity || "Unknown"}
    </span>
  );
}


function StatusBadge({ status }) {
  const value = status?.toLowerCase() || "unknown";

  return (
    <span className={`alert-badge event-${value}`}>
      {status || "Unknown"}
    </span>
  );
}


function Alerts() {
  const [activeAlerts, setActiveAlerts] = useState([]);
  const [summary, setSummary] = useState(null);
  const [history, setHistory] = useState([]);

  const [totalHistory, setTotalHistory] = useState(0);
  const [page, setPage] = useState(0);

  const [filters, setFilters] = useState({
    vehicle_id: "",
    alert_type: "",
    severity: "",
    event_status: "",
  });

  const [appliedFilters, setAppliedFilters] = useState({
    vehicle_id: "",
    alert_type: "",
    severity: "",
    event_status: "",
  });

  const [loading, setLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [historyError, setHistoryError] = useState("");

  const fetchLiveAlerts = useCallback(async () => {
    try {
      const [activeResponse, summaryResponse] = await Promise.all([
        getActiveAlerts(),
        getAlertSummary(),
      ]);

      setActiveAlerts(activeResponse.alerts || []);
      setSummary(summaryResponse);
      setError("");
    } catch (err) {
      console.error("Active alerts API error:", err);
      setError("Unable to load active alerts. Check backend connection.");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    setHistoryLoading(true);

    try {
      const response = await getAlertHistory({
        ...appliedFilters,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      });

      setHistory(response.alerts || []);
      setTotalHistory(response.total || 0);
      setHistoryError("");
    } catch (err) {
      console.error("Alert history API error:", err);
      setHistoryError("Unable to load alert history.");
    } finally {
      setHistoryLoading(false);
    }
  }, [appliedFilters, page]);

  useEffect(() => {
    fetchLiveAlerts();

    const interval = setInterval(fetchLiveAlerts, 10000);

    return () => clearInterval(interval);
  }, [fetchLiveAlerts]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleRefresh = async () => {
    setRefreshing(true);

    await Promise.all([
      fetchLiveAlerts(),
      fetchHistory(),
    ]);

    setRefreshing(false);
  };

  const handleFilterChange = (event) => {
    const { name, value } = event.target;

    setFilters((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleApplyFilters = () => {
    setPage(0);
    setAppliedFilters({ ...filters });
  };

  const handleClearFilters = () => {
    const emptyFilters = {
      vehicle_id: "",
      alert_type: "",
      severity: "",
      event_status: "",
    };

    setFilters(emptyFilters);
    setAppliedFilters(emptyFilters);
    setPage(0);
  };

  const totalPages = Math.max(
    1,
    Math.ceil(totalHistory / PAGE_SIZE)
  );

  return (
    <section className="dashboard-content alerts-page">

      {/* PAGE HEADING */}

      <div className="section-heading alerts-heading">
        <div>
          <h2>Fleet Alerts & Monitoring</h2>
          <p>
            Monitor operational exceptions and review vehicle alert history.
          </p>
        </div>

        <button
          className="refresh-analytics-button"
          onClick={handleRefresh}
          disabled={refreshing}
        >
          <RefreshCw
            size={16}
            className={refreshing ? "spinning" : ""}
          />
          Refresh
        </button>
      </div>

      {error && <p className="error-message">{error}</p>}

      {/* SUMMARY CARDS */}

      <div className="stats-grid alerts-stats">

        <div className="stat-card">
          <div className="stat-card-top">
            <span>Active Alerts</span>
            <span className="stat-icon blue">
              <BellRing size={20} />
            </span>
          </div>

          <p className="stat-value">
            {loading ? "..." : summary?.total_active_alerts ?? 0}
          </p>
        </div>

        <div className="stat-card">
          <div className="stat-card-top">
            <span>Critical Alerts</span>
            <span className="stat-icon orange">
              <ShieldAlert size={20} />
            </span>
          </div>

          <p className="stat-value alert-critical-number">
            {loading ? "..." : summary?.critical_alerts ?? 0}
          </p>
        </div>

        <div className="stat-card">
          <div className="stat-card-top">
            <span>Warnings</span>
            <span className="stat-icon orange">
              <AlertTriangle size={20} />
            </span>
          </div>

          <p className="stat-value alert-warning-number">
            {loading ? "..." : summary?.warning_alerts ?? 0}
          </p>
        </div>

        <div className="stat-card">
          <div className="stat-card-top">
            <span>Unknown Severity</span>
            <span className="stat-icon purple">
              <CircleCheck size={20} />
            </span>
          </div>

          <p className="stat-value">
            {loading ? "..." : summary?.unknown_severity_alerts ?? 0}
          </p>
        </div>
      </div>

      {/* ACTIVE ALERTS */}

      <div className="alerts-section">

        <div className="alerts-section-heading">
          <div>
            <h3>
              <BellRing size={19} />
              Active Alerts
            </h3>

            <p>Currently active fleet exceptions</p>
          </div>

          <span className="alerts-live-indicator">
            <span />
            Live monitoring
          </span>
        </div>

        {loading ? (
          <div className="alerts-empty-state">
            Loading active alerts...
          </div>
        ) : activeAlerts.length === 0 ? (
          <div className="alerts-empty-state">
            <CircleCheck size={28} />
            <strong>No active alerts</strong>
            <span>Your fleet currently has no active alerts.</span>
          </div>
        ) : (
          <div className="active-alert-grid">
            {activeAlerts.map((alert) => {
              const Icon = getAlertIcon(alert.alert_type);

              return (
                <div
                  className={`active-alert-card ${alert.severity?.toLowerCase() || "unknown"}`}
                  key={alert.alert_id}
                >
                  <div className="active-alert-top">
                    <div className="active-alert-icon">
                      <Icon size={20} />
                    </div>

                    <SeverityBadge severity={alert.severity} />
                  </div>

                  <h4>{getAlertLabel(alert.alert_type)}</h4>

                  <p className="active-alert-vehicle">
                    Vehicle: {alert.vehicle_id?.slice(0, 13) || "Unknown"}...
                  </p>

                  <div className="active-alert-value">
                    <span>Current value</span>
                    <strong>{formatValue(alert)}</strong>
                  </div>

                  <div className="active-alert-footer">
                    <Clock size={13} />
                    {formatDate(alert.event_time)}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* HISTORY */}

      <div className="alerts-section">

        <div className="alerts-section-heading">
          <div>
            <h3>
              <Clock size={19} />
              Alert History
            </h3>

            <p>Historical triggered and resolved alert events</p>
          </div>

          <span className="history-total">
            {totalHistory} records
          </span>
        </div>

        {/* FILTERS */}

        <div className="alerts-filter-panel">

          <div className="alerts-filter-field vehicle-search">
            <Search size={17} />

            <input
              type="text"
              name="vehicle_id"
              placeholder="Search vehicle ID..."
              value={filters.vehicle_id}
              onChange={handleFilterChange}
            />
          </div>

          <select
            name="alert_type"
            value={filters.alert_type}
            onChange={handleFilterChange}
          >
            <option value="">All Alert Types</option>
            <option value="LOW_FUEL">Low Fuel</option>
            <option value="OVERSPEED">Overspeed</option>
            <option value="INACTIVE">Inactive Vehicle</option>
            <option value="PROLONGED_IDLE">Prolonged Idle</option>
          </select>

          <select
            name="severity"
            value={filters.severity}
            onChange={handleFilterChange}
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="WARNING">Warning</option>
          </select>

          <select
            name="event_status"
            value={filters.event_status}
            onChange={handleFilterChange}
          >
            <option value="">All Events</option>
            <option value="TRIGGERED">Triggered</option>
            <option value="RESOLVED">Resolved</option>
          </select>

          <button
            className="alerts-apply-button"
            onClick={handleApplyFilters}
          >
            Apply
          </button>

          <button
            className="alerts-clear-button"
            onClick={handleClearFilters}
          >
            Clear
          </button>
        </div>

        {historyError && (
          <p className="error-message">{historyError}</p>
        )}

        {/* HISTORY TABLE */}

        <div className="vehicle-table-container alerts-table-container">
          <table className="vehicle-table alerts-table">
            <thead>
              <tr>
                <th>Vehicle ID</th>
                <th>Alert Type</th>
                <th>Severity</th>
                <th>Current Value</th>
                <th>Threshold</th>
                <th>Event Status</th>
                <th>Event Time</th>
              </tr>
            </thead>

            <tbody>
              {historyLoading ? (
                <tr>
                  <td colSpan="7">Loading alert history...</td>
                </tr>
              ) : history.length === 0 ? (
                <tr>
                  <td colSpan="7">
                    No alert history found for these filters.
                  </td>
                </tr>
              ) : (
                history.map((alert) => (
                  <tr key={alert.event_id}>
                    <td className="alert-vehicle-id">
                      {alert.vehicle_id?.slice(0, 13)}...
                    </td>

                    <td>{getAlertLabel(alert.alert_type)}</td>

                    <td>
                      <SeverityBadge severity={alert.severity} />
                    </td>

                    <td>{formatValue(alert)}</td>

                    <td>
                      {alert.threshold == null
                        ? "—"
                        : alert.alert_type === "LOW_FUEL"
                          ? `${Number(alert.threshold).toFixed(1)}%`
                          : alert.alert_type === "OVERSPEED"
                            ? `${Number(alert.threshold).toFixed(1)} km/h`
                            : `${Number(alert.threshold).toFixed(0)} sec`}
                    </td>

                    <td>
                      <StatusBadge status={alert.event_status} />
                    </td>

                    <td>{formatDate(alert.event_time)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* PAGINATION */}

        <div className="alerts-pagination">
          <span>
            Showing {history.length} of {totalHistory} events
          </span>

          <div>
            <button
              onClick={() => setPage((previous) => Math.max(0, previous - 1))}
              disabled={page === 0 || historyLoading}
              aria-label="Previous page"
            >
              <ChevronLeft size={17} />
              Previous
            </button>

            <span>
              Page {page + 1} of {totalPages}
            </span>

            <button
              onClick={() => setPage((previous) =>
                Math.min(totalPages - 1, previous + 1)
              )}
              disabled={page >= totalPages - 1 || historyLoading}
              aria-label="Next page"
            >
              Next
              <ChevronRight size={17} />
            </button>
          </div>
        </div>

      </div>
    </section>
  );
}

export default Alerts;
