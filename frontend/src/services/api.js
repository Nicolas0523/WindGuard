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
  analyze: async (polygon, startDate, endDate) => {
    const geoJson = formatToGeoJSON(polygon);
    const payload = {
      ...geoJson,
      start_date: startDate,
      end_date: endDate,
    };
    
    const response = await apiClient.post("/analyze", payload);
    const { task_id } = response.data;

    return await pollTaskStatus(task_id);
  },

  forecastShort: async (polygon) => {
    const geoJson = formatToGeoJSON(polygon);
    const payload = {
      ...geoJson,
      start_date: "",
      end_date: "",
    };
    
    const response = await apiClient.post("/analyze/short", payload);
    const { task_id } = response.data;

    return await pollTaskStatus(task_id);
  },

  analyzeClimate: async (polygon, startDate) => {
    const geoJson = formatToGeoJSON(polygon);
    const payload = {
      ...geoJson,
      start_date: startDate,
      end_date: "",
    };
    
    const response = await apiClient.post("/analyze/climate", payload);
    const data = response.data;

    if (data.status === "completed") {
      return data.result;
    }

    return await pollTaskStatus(data.task_id);
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