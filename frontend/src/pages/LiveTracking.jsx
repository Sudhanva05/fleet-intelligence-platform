
import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { MapPin } from "lucide-react";

import api from "../services/api";
import FleetMap from "../components/FleetMap";

function LiveTracking() {
  const location = useLocation();

  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Vehicle selected from the Vehicle Management page
  const selectedVehicle = location.state?.selectedVehicle ?? null;

  useEffect(() => {
    let cancelled = false;

    const fetchVehicles = async () => {
      try {
        const response = await api.get("/vehicles/");

        if (!cancelled) {
          setVehicles(response.data.vehicles ?? []);
          setError("");
        }
      } catch (err) {
        console.error("Live tracking API error:", err);

        if (!cancelled) {
          setError("Unable to load vehicle locations.");
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

  return (
    <section className="dashboard-content">
      <div className="section-heading">
        <div>
          <h2>Live Fleet Tracking</h2>
          <p>Monitor vehicle locations across the fleet.</p>
        </div>
      </div>

      {selectedVehicle && (
        <div className="tracking-selected-vehicle">
          <MapPin size={20} />
          <span>
            Selected vehicle: <strong>
              {selectedVehicle.vehicle_id.slice(0, 8)}
            </strong>
          </span>
        </div>
      )}

      {error && <p className="error-message">{error}</p>}

      {loading ? (
        <p>Loading vehicle locations...</p>
      ) : (
        <FleetMap
          vehicles={vehicles}
          focusedVehicle={selectedVehicle}
        />
      )}
    </section>
  );
}

export default LiveTracking;
