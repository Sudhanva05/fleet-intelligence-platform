
import { useEffect, useMemo } from "react";
import {
  MapContainer,
  TileLayer,
  Polyline,
  Marker,
  Popup,
  CircleMarker,
  useMap,
} from "react-leaflet";

import L from "leaflet";
import "leaflet/dist/leaflet.css";

const vehicleIcon = L.divIcon({
  className: "historical-vehicle-marker",
  html: `<div style="
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #0ea5e9;
    border: 3px solid white;
    border-radius: 50%;
    font-size: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.4);
  ">🚚</div>`,
  iconSize: [36, 36],
  iconAnchor: [18, 18],
});

function FitRouteBounds({ positions }) {
  const map = useMap();

  useEffect(() => {
    if (positions.length === 1) {
      map.setView(positions[0], 16);
      return;
    }

    if (positions.length > 1) {
      map.fitBounds(positions, {
        padding: [40, 40],
        maxZoom: 16,
      });
    }
  }, [map, positions]);

  return null;
}

function HistoricalRouteMap({
  history = [],
  currentIndex = 0,
}) {
  const validHistory = useMemo(
    () =>
      history.filter(
        (record) =>
          Number.isFinite(Number(record.latitude)) &&
          Number.isFinite(Number(record.longitude))
      ),
    [history]
  );

  const positions = useMemo(
    () =>
      validHistory.map((record) => [
        Number(record.latitude),
        Number(record.longitude),
      ]),
    [validHistory]
  );

  if (validHistory.length === 0) {
    return (
      <div className="historical-map-empty">
        No GPS coordinates available for this journey.
      </div>
    );
  }

  const safeIndex = Math.min(
    Math.max(currentIndex, 0),
    validHistory.length - 1
  );

  const currentRecord = validHistory[safeIndex];

  return (
    <div
      className="historical-route-map"
      style={{ height: "500px", width: "100%" }}
    >
      <MapContainer
        center={positions[0]}
        zoom={14}
        scrollWheelZoom={true}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <FitRouteBounds positions={positions} />

        {/* Complete historical route */}
        {positions.length > 1 && (
          <Polyline
            positions={positions}
            pathOptions={{
              color: "#0ea5e9",
              weight: 5,
              opacity: 0.85,
            }}
          />
        )}

        {/* Starting location */}
        <CircleMarker
          center={positions[0]}
          radius={8}
          pathOptions={{
            color: "#ffffff",
            fillColor: "#22c55e",
            fillOpacity: 1,
          }}
        >
          <Popup>Journey Start</Popup>
        </CircleMarker>

        {/* Ending location */}
        {positions.length > 1 && (
          <CircleMarker
            center={positions[positions.length - 1]}
            radius={8}
            pathOptions={{
              color: "#ffffff",
              fillColor: "#ef4444",
              fillOpacity: 1,
            }}
          >
            <Popup>Journey End</Popup>
          </CircleMarker>
        )}

        {/* Current playback vehicle */}
        <Marker
          position={[
            Number(currentRecord.latitude),
            Number(currentRecord.longitude),
          ]}
          icon={vehicleIcon}
        >
          <Popup>
            <strong>Historical Vehicle</strong>
            <p>Speed: {Number(currentRecord.speed).toFixed(1)} km/h</p>
            <p>Fuel: {Number(currentRecord.fuel_level).toFixed(1)}%</p>
            <p>Heading: {Number(currentRecord.heading).toFixed(1)}°</p>
            <p>Time: {currentRecord.timestamp}</p>
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}

export default HistoricalRouteMap;
