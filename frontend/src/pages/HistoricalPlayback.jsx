import HistoricalRouteMap from "../components/HistoricalRouteMap";
import { useEffect, useState } from "react";
import {
  Car,
  Calendar,
  Search,
  LoaderCircle,
  Play,
  Pause,
  RotateCcw,
} from "lucide-react";
import { getAnalyticsVehicles, getVehicleHistory } from "../services/api";

function HistoricalPlayback() {
  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState("");

  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");

  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);

  useEffect(() => {
    const fetchVehicles = async () => {
      try {
        const data = await getAnalyticsVehicles();
        setVehicles(data.vehicles ?? []);
      } catch (err) {
        setError("Unable to load historical vehicles.");
      }
    };

    fetchVehicles();
  }, []);

  // Automatically advance through historical telemetry records.
  useEffect(() => {
    if (!isPlaying || history.length < 2) return;

    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) =>
        Math.min(prevIndex + 1, history.length - 1)
      );
    }, 500 / playbackSpeed);

    return () => clearInterval(interval);
  }, [isPlaying, history.length, playbackSpeed]);

  // Stop playback when the final record is reached.
  useEffect(() => {
    if (
      history.length > 0 &&
      currentIndex >= history.length - 1
    ) {
      setIsPlaying(false);
    }
  }, [currentIndex, history.length]);

  const handleSearch = async () => {
    if (!selectedVehicle) {
      setError("Please select a vehicle.");
      return;
    }

    if (!startTime || !endTime) {
      setError("Please select both start and end times.");
      return;
    }

    if (new Date(startTime) > new Date(endTime)) {
      setError("Start time must be before end time.");
      return;
    }

    setLoading(true);
    setError("");
    setHistory([]);
    setCurrentIndex(0);
    setIsPlaying(false);
    setHasSearched(true);

    try {
      const data = await getVehicleHistory(
        selectedVehicle,
        startTime,
        endTime
      );

      setHistory(data.history ?? []);
      setCurrentIndex(0);
    } catch (err) {
      if (err.response?.status === 404) {
        setError("No historical records found in this time range.");
      } else {
        setError("Unable to retrieve vehicle history.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePlayPause = () => {
    if (history.length < 2) return;

    if (isPlaying) {
      setIsPlaying(false);
    } else {
      if (currentIndex >= history.length - 1) {
        setCurrentIndex(0);
      }

      setIsPlaying(true);
    }
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentIndex(0);
  };

  const handleTimelineChange = (event) => {
    setIsPlaying(false);
    setCurrentIndex(Number(event.target.value));
  };

  const currentRecord = history[currentIndex];

  return (
    <section className="dashboard-content">
      <div className="section-heading">
        <div>
          <h2>Historical Playback</h2>
          <p>Replay historical vehicle journeys and telemetry.</p>
        </div>
      </div>

      {/* Vehicle and Date Filters */}
      <div className="playback-filter-panel">
        <div className="playback-field">
          <label>
            <Car size={17} /> Select Vehicle
          </label>

          <select
            value={selectedVehicle}
            onChange={(e) => setSelectedVehicle(e.target.value)}
          >
            <option value="">Choose a vehicle</option>

            {vehicles.map((vehicle) => (
              <option key={vehicle} value={vehicle}>
                {vehicle}
              </option>
            ))}
          </select>
        </div>

        <div className="playback-field">
          <label>
            <Calendar size={17} /> Start Date & Time
          </label>

          <input
            type="datetime-local"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
          />
        </div>

        <div className="playback-field">
          <label>
            <Calendar size={17} /> End Date & Time
          </label>

          <input
            type="datetime-local"
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
          />
        </div>

        <button
          className="playback-search-button"
          onClick={handleSearch}
          disabled={loading}
        >
          {loading ? (
            <LoaderCircle size={18} />
          ) : (
            <Search size={18} />
          )}

          {loading ? "Loading..." : "Load History"}
        </button>
      </div>

      {error && <p className="error-message">{error}</p>}

      {/* Historical Results */}
      {hasSearched && !loading && !error && (
        <div className="playback-results">
          <h3>Historical Records</h3>

          <p>{history.length} telemetry records retrieved.</p>

          {history.length > 0 && (
            <>
              {/* Current Vehicle Telemetry */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
                  gap: "16px",
                  margin: "20px 0",
                }}
              >
                <div className="playback-field">
                  <label>Current Timestamp</label>
                  <strong>
                    {currentRecord?.timestamp ?? "-"}
                  </strong>
                </div>

                <div className="playback-field">
                  <label>Vehicle Speed</label>
                  <strong>
                    {Number(currentRecord?.speed ?? 0).toFixed(1)} km/h
                  </strong>
                </div>

                <div className="playback-field">
                  <label>Fuel Level</label>
                  <strong>
                    {Number(currentRecord?.fuel_level ?? 0).toFixed(1)}%
                  </strong>
                </div>

                <div className="playback-field">
                  <label>Record</label>
                  <strong>
                    {currentIndex + 1} / {history.length}
                  </strong>
                </div>
              </div>

              {/* Playback Controls */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  flexWrap: "wrap",
                  margin: "20px 0",
                }}
              >
                <button
                  className="playback-search-button"
                  onClick={handlePlayPause}
                  disabled={history.length < 2}
                >
                  {isPlaying ? (
                    <Pause size={18} />
                  ) : (
                    <Play size={18} />
                  )}

                  {isPlaying ? "Pause" : "Play"}
                </button>

                <button
                  className="playback-search-button"
                  onClick={handleReset}
                >
                  <RotateCcw size={18} />
                  Reset
                </button>

                <div className="playback-field">
                  <label>Playback Speed</label>

                  <select
                    value={playbackSpeed}
                    onChange={(e) =>
                      setPlaybackSpeed(Number(e.target.value))
                    }
                  >
                    <option value={1}>1x</option>
                    <option value={2}>2x</option>
                    <option value={4}>4x</option>
                  </select>
                </div>
              </div>

              {/* Timeline Slider */}
              <div style={{ margin: "20px 0" }}>
                <label
                  style={{
                    display: "block",
                    marginBottom: "10px",
                  }}
                >
                  Journey Timeline
                </label>

                <input
                  type="range"
                  min="0"
                  max={history.length - 1}
                  value={currentIndex}
                  onChange={handleTimelineChange}
                  style={{
                    width: "100%",
                    cursor: "pointer",
                  }}
                />

                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: "13px",
                  }}
                >
                  <span>Record 1</span>
                  <span>Record {history.length}</span>
                </div>
              </div>

              {/* Historical Route Map */}
              <div className="playback-map-section">
                <h3>Vehicle Journey</h3>

                <HistoricalRouteMap
                  history={history}
                  currentIndex={currentIndex}
                />
              </div>

              {/* Historical Telemetry Records */}
              <div className="playback-record-list">
                {history.slice(0, 5).map((record, index) => (
                  <div
                    key={`${record.timestamp}-${index}`}
                    onClick={() => {
                      setIsPlaying(false);
                      setCurrentIndex(index);
                    }}
                    onKeyDown={(event) => {
                      if (
                        event.key === "Enter" ||
                        event.key === " "
                      ) {
                        setIsPlaying(false);
                        setCurrentIndex(index);
                      }
                    }}
                    role="button"
                    tabIndex={0}
                    aria-pressed={currentIndex === index}
                    style={{
                      cursor: "pointer",
                      outline:
                        currentIndex === index
                          ? "2px solid #0ea5e9"
                          : "none",
                    }}
                  >
                    <strong>{record.timestamp}</strong>

                    <span>
                      Speed: {Number(record.speed).toFixed(1)} km/h
                    </span>

                    <span>
                      Fuel: {Number(record.fuel_level).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}

export default HistoricalPlayback;