import { useState } from "react";
import { api } from "../services/api";

export function useAnalysis() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Запуск анализа в зависимости от выбранного типа
   */
  const executeAnalysis = async (polygon, startDate, endDate, analysisType = "historical") => {
    if (!polygon || polygon.length === 0) {
      setError("Please draw a polygon on the map first.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let data;
      switch (analysisType) {
        case "short":
          data = await api.forecastShort(polygon);
          break;
        case "climate":
          data = await api.analyzeClimate(polygon, startDate);
          break;
        case "historical":
        default:
          data = await api.analyze(polygon, startDate, endDate);
          break;
      }

      if (data && data.error) {
        setError(data.error);
        setAnalysis(null);
      } else {
        setAnalysis(data);
      }
    } catch (err) {
      console.error("Analysis request failed:", err);
      setError(err.response?.data?.detail || "Failed to complete wind erosion analysis.");
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  return {
    analysis,
    loading,
    error,
    executeAnalysis,
    setAnalysis,
  };
}