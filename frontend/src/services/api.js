
import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 10000,
});

// --------------------------------------------------
// VEHICLE SUMMARY
// --------------------------------------------------

export const getVehicleSummary = async () => {
  const response = await api.get("/vehicles/summary");
  return response.data;
};

// --------------------------------------------------
// FLEET ANALYTICS
// --------------------------------------------------

export const getFleetOverview = async (startTime, endTime) => {
  const response = await api.get("/analytics/overview", {
    params: {
      start_time: startTime || undefined,
      end_time: endTime || undefined,
    },
  });

  return response.data;
};

export const getFleetSpeedTrend = async (startTime, endTime) => {
  const response = await api.get("/analytics/speed", {
    params: {
      start_time: startTime || undefined,
      end_time: endTime || undefined,
    },
  });

  return response.data;
};

export const getFleetFuelTrend = async (startTime, endTime) => {
  const response = await api.get("/analytics/fuel", {
    params: {
      start_time: startTime || undefined,
      end_time: endTime || undefined,
    },
  });

  return response.data;
};

// --------------------------------------------------
// ANALYTICS VEHICLES
// --------------------------------------------------

export const getAnalyticsVehicles = async () => {
  const response = await api.get("/analytics/vehicles");
  return response.data;
};

// --------------------------------------------------
// VEHICLE HISTORICAL DATA
// --------------------------------------------------

export const getVehicleHistory = async (
  vehicleId,
  startTime,
  endTime
) => {
  const response = await api.get(
    `/analytics/vehicle/${vehicleId}/history`,
    {
      params: {
        start_time: startTime || undefined,
        end_time: endTime || undefined,
      },
    }
  );

  return response.data;
};

export default api;
