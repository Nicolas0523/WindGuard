import axios from "axios";

const API_BASE_URL = "https://windguard-1.onrender.com/";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Helper to format Leaflet coordinates [[lat, lng], ...] 
 * into a valid GeoJSON Polygon [[[lng, lat], ...]] with a closed ring.
 */
const formatToGeoJSON = (latLngs) => {
  if (!latLngs || latLngs.length === 0) return null;

  // Leaflet uses [lat, lng]. GeoJSON standard requires [lng, lat]
  const coordinates = latLngs.map((point) => [point[1], point[0]]);

  // Close the polygon ring (first point must equal the last point)
  const firstPoint = coordinates[0];
  const lastPoint = coordinates[coordinates.length - 1];
  if (firstPoint[0] !== lastPoint[0] || firstPoint[1] !== lastPoint[1]) {
    coordinates.push([firstPoint[0], firstPoint[1]]);
  }

  return {
    geometry: {
      type: "Polygon",
      coordinates: [coordinates], // Triple nested array
    },
  };
};

export const api = {
  // 1. Standard Historical Analysis (GEE)
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

  // 2. 10-Day Short-term Forecast
  forecastShort: async (polygon) => {
    const geoJson = formatToGeoJSON(polygon);
    const payload = {
      ...geoJson,
      start_date: "", // Schema requirement; backend will resolve actual dates
      end_date: "",
    };
    const response = await apiClient.post("/analyze/short", payload);
    return response.data;
  },

  // 3. Climate Scenario 2040-2050 (SSP5-8.5)
  analyzeClimate: async (polygon, startDate) => {
    const geoJson = formatToGeoJSON(polygon);
    const payload = {
      ...geoJson,
      start_date: startDate, // Used on backend to parse the active month
      end_date: "",
    };
    const response = await apiClient.post("/analyze/climate", payload);
    return response.data;
  },

  // 4. Personalized AI Assistant Query (Gemini with Fallbacks)
  askAssistant: async (question, analysisData = null) => {
    // Format payload to strictly match the backend's ChatRequest Pydantic model
    const payload = {
      message: question, // Backend: ChatRequest.message
      analysis_data: analysisData
        ? {
            risk_score: analysisData.risk_score,
            total_cells: analysisData.grid?.length || 0,
            // Filter out NaNs and pass top 5 highest-risk cells for location-specific context
            worst_cells: [...(analysisData.grid || [])]
              .filter((cell) => cell.risk !== undefined && !isNaN(cell.risk))
              .sort((a, b) => b.risk - a.risk)
              .slice(0, 5),
            hotspots_count: analysisData.hotspots?.length || 0,
          }
        : null, // Backend: ChatRequest.analysis_data
    };

    const response = await apiClient.post("/api/chat", payload);
    return response.data; // Returns {"response": "AI Markdown text response"}
  },
};