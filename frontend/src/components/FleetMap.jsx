
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Default vehicle marker
const vehicleIcon = L.divIcon({
  className: "vehicle-marker",
  html: `<div class="vehicle-marker-inner">🚚</div>`,
  iconSize: [36, 36],
  iconAnchor: [18, 18],
  popupAnchor: [0, -18],
});

function FleetMap({ vehicles = [] }) {
  const validVehicles = vehicles.filter(
    (vehicle) =>
      Number.isFinite(Number(vehicle.latitude)) &&
      Number.isFinite(Number(vehicle.longitude))
  );

  return (
    <div className="fleet-map">
      <MapContainer
        center={[12.9716, 77.5946]}
        zoom={11}
        scrollWheelZoom={true}
        style={{ height: "450px", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {validVehicles.map((vehicle) => (
          <Marker
            key={vehicle.vehicle_id}
            position={[
              Number(vehicle.latitude),
              Number(vehicle.longitude),
            ]}
            icon={vehicleIcon}
          >
            <Popup>
              <strong>Vehicle</strong>
              <p>ID: {vehicle.vehicle_id.slice(0, 8)}</p>
              <p>Speed: {Number(vehicle.speed).toFixed(1)} km/h</p>
              <p>Fuel: {Number(vehicle.fuel_level).toFixed(1)}%</p>
              <p>Status: {vehicle.status}</p>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}

export default FleetMap;
