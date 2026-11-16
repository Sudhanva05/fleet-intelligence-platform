
import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 10000,
});

export const getVehicleSummary = async () => {
  const response = await api.get("/vehicles/summary");
  return response.data;
};

export const getFleetOverview = async () => {
  const response = await api.get("/analytics/overview");
  return response.data;
};


export const getAnalyticsVehicles = async () => {
  const response = await api.get("/analytics/vehicles");
  return response.data;
};

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
