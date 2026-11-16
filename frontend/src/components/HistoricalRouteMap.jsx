import { useEffect, useMemo, useState } from "react";
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

// Smoothly animate the vehicle between GPS coordinates.
function AnimatedVehicle({
  targetPosition,
  currentRecord,
  autoFollow,
}) {
  const map = useMap();

  const [position, setPosition] = useState(targetPosition);

  useEffect(() => {
    if (!targetPosition) return;

    const startPosition = position;
    const endPosition = targetPosition;

    const duration = 450;
    let animationFrame;
    let startTime = null;

    const animate = (timestamp) => {
      if (startTime === null) {
        startTime = timestamp;
      }

      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Smooth ease-in-out interpolation.
      const eased =
        progress < 0.5
          ? 2 * progress * progress
          : 1 - Math.pow(-2 * progress + 2, 2) / 2;

      const latitude =
        startPosition[0] +
        (endPosition[0] - startPosition[0]) * eased;

      const longitude =
        startPosition[1] +
        (endPosition[1] - startPosition[1]) * eased;

      const newPosition = [latitude, longitude];

      setPosition(newPosition);

      // Keep the map centered on the vehicle when enabled.
      if (autoFollow) {
        map.setView(newPosition, map.getZoom(), {
          animate: false,
        });
      }

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animationFrame);
    };

    // Position is intentionally the starting point for each animation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetPosition, autoFollow, map]);

  return (
    <Marker position={position} icon={vehicleIcon}>
      <Popup>
        <strong>Historical Vehicle</strong>

        <p>
          Speed: {Number(currentRecord.speed).toFixed(1)} km/h
        </p>

        <p>
          Fuel: {Number(currentRecord.fuel_level).toFixed(1)}%
        </p>

        <p>
          Heading: {Number(currentRecord.heading).toFixed(1)}°
        </p>

        <p>Time: {currentRecord.timestamp}</p>
      </Popup>
    </Marker>
  );
}

function HistoricalRouteMap({
  history = [],
  currentIndex = 0,
}) {
  const [autoFollow, setAutoFollow] = useState(true);

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

  const targetPosition = [
    Number(currentRecord.latitude),
    Number(currentRecord.longitude),
  ];

  return (
    <div
      className="historical-route-map"
      style={{
        height: "500px",
        width: "100%",
        position: "relative",
      }}
    >
      {/* Auto-follow control */}
      <button
        onClick={() => setAutoFollow((previous) => !previous)}
        style={{
          position: "absolute",
          top: "12px",
          right: "12px",
          zIndex: 1000,
          padding: "9px 14px",
          border: "none",
          borderRadius: "8px",
          background: autoFollow ? "#0ea5e9" : "#ffffff",
          color: autoFollow ? "#ffffff" : "#1f2937",
          fontWeight: 600,
          cursor: "pointer",
          boxShadow: "0 2px 8px rgba(0,0,0,0.25)",
        }}
      >
        {autoFollow ? "Auto-follow: ON" : "Auto-follow: OFF"}
      </button>

      <MapContainer
        center={positions[0]}
        zoom={14}
        scrollWheelZoom={true}
        style={{
          height: "100%",
          width: "100%",
        }}
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

        {/* Animated playback vehicle */}
        <AnimatedVehicle
          targetPosition={targetPosition}
          currentRecord={currentRecord}
          autoFollow={autoFollow}
        />
      </MapContainer>
    </div>
  );
}

export default HistoricalRouteMap;