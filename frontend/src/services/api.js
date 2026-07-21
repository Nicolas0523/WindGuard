import axios from "axios";

const API_BASE_URL = "https://windguard-1.onrender.com/";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});


const formatToGeoJSON = (latLngs) => {
  if (!latLngs || latLngs.length === 0) return null;

  const coordinates = latLngs.map((point) => [point[1], point[0]]);

  const firstPoint = coordinates[0];
  const lastPoint = coordinates[coordinates.length - 1];
  if (firstPoint[0] !== lastPoint[0] || firstPoint[1] !== lastPoint[1]) {
    coordinates.push([firstPoint[0], firstPoint[1]]);
  }

  return {
    geometry: {
      type: "Polygon",
      coordinates: [coordinates], 
    },
  };
};

export const api = {
  getStatus: async (jobId) => {
    const response = await apiClient.get(`/analyze/status/${jobId}`);
    return response.data();
  },

  analyze: async (polygon, startDate, endDate) => {
    const geoJson = formatToGeoJSON(polygon);
    const payload = {
      ...geoJson,
      start_date: startDate,
      end_date: endDate,
    };
    const response = await apiClient.post("/analyze", payload);
    return response.data;
  },

  forecastShort: async (polygon) => {
    const geoJson = formatToGeoJSON(polygon);
    const payload = {
      ...geoJson,
      start_date: "", 
      end_date: "",
    };
    const response = await apiClient.post("/analyze/short", payload);
    return response.data;
  },

  analyzeClimate: async (polygon, startDate) => {
    const geoJson = formatToGeoJSON(polygon);
    const payload = {
      ...geoJson,
      start_date: startDate, 
      end_date: "",
    };
    const response = await apiClient.post("/analyze/climate", payload);
    return response.data;
  },

  askAssistant: async (question, analysisData = null) => {
    const payload = {
      message: question, 
      analysis_data: analysisData
        ? {
            risk_score: analysisData.risk_score,
            total_cells: analysisData.grid?.length || 0,
            worst_cells: [...(analysisData.grid || [])]
              .filter((cell) => cell.risk !== undefined && !isNaN(cell.risk))
              .sort((a, b) => b.risk - a.risk)
              .slice(0, 5),
            hotspots_count: analysisData.hotspots?.length || 0,
          }
        : null, 
    };

    const response = await apiClient.post("/api/chat", payload);
    return response.data; 
  },
};