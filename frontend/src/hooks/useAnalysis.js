import { useState } from "react";
import { api } from "../services/api";

const POLL_INTERVAL = 2000;
const POLL_TIMEOUT = 120000;

async function pollStatus(jobId) {
  const start = Date.now()
  
  while (Date.now() - start < POLL_TIMEOUT) {
    await new Promise(r => setTimeout(r, POLL_INTERVAL)); 

    const status = await api.getStatus(jobId);
    if (status.status === "done") return status;
    if (status.status === "error") throw new Error(status.error);
  }

  throw new Error("Analysis timed out. Please try again.");
}

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
      let response;
      switch (analysisType) {
        case "short":
          response = await api.forecastShort(polygon);
          break;
        case "climate":
          response = await api.analyzeClimate(polygon, startDate);
          break;
        default:
          response = await api.analyze(polygon, startDate, endDate);
      }

      if (response.error) {
        setError(response.error);
        return;
      }

      const result = await pollStatus(response.job_id);

      if (result.error) {
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