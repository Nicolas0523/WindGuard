import { useState } from "react";

export function ControlPanel({ onRunAnalysis, loading, polygon }) {
  const [startDate, setStartDate] = useState("2024-01-01");
  const [endDate, setEndDate] = useState("2024-12-31");
  const [analysisType, setAnalysisType] = useState("historical"); // 'historical' | 'short' | 'climate'

  const handleAnalyzeClick = () => {
    onRunAnalysis(polygon, startDate, endDate, analysisType);
  };

  return (
    <div className="control-panel glass-panel">
      <h3 className="panel-title">Wind Erosion Analysis</h3>
      
      {/* Выбор типа анализа */}
      <div className="input-group">
        <label>Analysis Type</label>
        <select 
          className="custom-input" 
          value={analysisType} 
          onChange={(e) => setAnalysisType(e.target.value)}
        >
          <option value="historical">Historical Analysis</option>
          <option value="short">10-Day Forecast</option>
          <option value="climate">Climate Scenario (2040-2050)</option>
        </select>
      </div>

      {/* Показываем поля ввода дат только если выбран НЕ 10-дневный прогноз */}
      {analysisType !== "short" && (
        <>
          <div className="input-group">
            <label>Start Date</label>
            <input 
              type="date" 
              className="custom-input" 
              value={startDate} 
              onChange={(e) => setStartDate(e.target.value)} 
            />
          </div>
          <div className="input-group">
            <label>End Date</label>
            <input 
              type="date" 
              className="custom-input" 
              value={endDate} 
              onChange={(e) => setEndDate(e.target.value)} 
            />
          </div>
        </>
      )}

      {/* КНОПКА ЗАПУСКА АНАЛИЗА */}
      <button
        className="btn-analyze"
        disabled={loading || !polygon} 
        onClick={handleAnalyzeClick}
      >
        {loading ? "Analyzing..." : "Run AI Analysis"}
      </button>

      {/* Информационное сообщение, если фигура еще не нарисована */}
      {!polygon && (
        <p style={{ fontSize: '9.5px', color: '#64748b', marginTop: '6px', textAlign: 'center' }}>
          * Draw a polygon on the map to unlock analysis
        </p>
      )}
    </div>
  );
}