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

  const coordinates = latLngs.map((point) => [point[1], point[0]]);

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

const pollTaskStatus = async (taskId) => {
  const pollInterval = 3000; 

  while (true) {
    const response = await apiClient.get(`/analyze/status/${taskId}`);
    const task = response.data;

    if (task.status === "completed") {
      return task.result;
    }

    if (task.status === "error") {
      throw new Error(task.error || "Analysis failed on server.");
    }

    await new Promise((resolve) => setTimeout(resolve, pollInterval));
  }
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
    return await pollTaskStatus(response.data.task_id);
  },

  forecastShort: async (polygon) => {
    const geoJson = formatToGeoJSON(polygon);
    const payload = {
      ...geoJson,
      start_date: "", // Schema requirement; backend will resolve actual dates
      end_date: "",
    };
    
    const response = await apiClient.post("/analyze/short", payload);
    return await pollTaskStatus(response.data.task_id);
  },

  analyzeClimate: async (polygon, startDate) => {
    const geoJson = formatToGeoJSON(polygon);
    const payload = {
      ...geoJson,
      start_date: startDate, // Used on backend to parse the active month
      end_date: "",
    };
    
    const response = await apiClient.post("/analyze/climate", payload);
    if (response.data.status === "completed") {
      return response.data.result;
    }
    return await pollTaskStatus(response.data.task_id);
  },

  askAssistant: async (question, analysisData = null) => {
    const payload = {
      message: question, // Backend: ChatRequest.message
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
        : null, // Backend: ChatRequest.analysis_data
    };

    const response = await apiClient.post("/api/chat", payload);
    return response.data; // Returns {"response": "AI Markdown text response"}
  },
};