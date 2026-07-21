import { useState } from "react";
import { api, pollTaskStatus } from "../services/api";

export function useAnalysis() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);

  const executeAnalysis = async (polygon, startDate, endDate, analysisType = "historical") => {
    if (!polygon || polygon.length === 0) {
      setError("Please draw a polygon on the map first.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let result;
      
      switch (analysisType) {
        case "short":
          result = await api.forecastShort(polygon, startDate, endDate);
          break;
        case "climate":
          result = await api.analyzeClimate(polygon, startDate, endDate);
          break;
        default:
          result = await api.analyze(polygon, startDate, endDate);
      }

      if (result?.error) {
        setError(result.error);
        setAnalysis(null);
      } else {
        setAnalysis(result);
      }

    } catch (err) {
      console.error("Analysis failed:", err);
      setError(err.message || "Failed to complete analysis.");
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  return { analysis, loading, error, executeAnalysis, setAnalysis };
}