import React from "react";

export default function HotspotList({ analysis }) {
  if (!analysis) return null;

  // 1. Пытаемся взять готовые хотспоты от бэкенда
  let hotspots = analysis.hotspots || [];

  // 2. БУЛЛЕТПРОФ ФОЛБЕК: Если бэкенд не прислал хотспоты, мы вычисляем их сами из сетки (grid)
  if (hotspots.length === 0 && analysis.grid && analysis.grid.length > 0) {
    // Сортируем ячейки сетки по убыванию риска и берем ТОП-5 самых критических
    hotspots = [...analysis.grid]
      .filter(cell => cell.risk !== undefined && !isNaN(cell.risk))
      .sort((a, b) => b.risk - a.risk)
      .slice(0, 5) // Берем топ-5
      .map((cell, idx) => ({
        lat: cell.lat,
        lon: cell.lon,
        // Сохраняем значение риска
        risk: cell.risk,
        max_risk: cell.risk 
      }));
  }

  // Если вообще никаких данных нет (ни сетки, ни хотспотов) — только тогда скрываем
  if (hotspots.length === 0) {
    return (
      <div className="hotspots-card glass-panel" style={{ marginTop: "16px", padding: "12px", width: "100%" }}>
        <span style={{ fontSize: "10px", fontWeight: "600", color: "#94a3b8" }}>CRITICAL HOTSPOTS</span>
        <div style={{ color: "#ef4444", fontSize: "11.5px", marginTop: "8px" }}>No high-risk zones detected.</div>
      </div>
    );
  }

  return (
    <div 
      className="hotspots-card glass-panel" 
      style={{ 
        marginTop: "16px", 
        padding: "12px",
        width: "100%",
        boxSizing: "border-box"
      }}
    >
      <div className="hotspots-header" style={{ marginBottom: "8px" }}>
        <span 
          className="hotspots-title" 
          style={{ 
            fontSize: "10px", 
            fontWeight: "600", 
            color: "#94a3b8", 
            letterSpacing: "1px" 
          }}
        >
          CRITICAL HOTSPOTS
        </span>
      </div>

      <div className="hotspots-list" style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        {hotspots.map((spot, idx) => {
          // Вытаскиваем значение риска из любых возможных полей
          const rawRisk = 
            spot.max_risk !== undefined ? spot.max_risk :
            spot.risk !== undefined ? spot.risk :
            spot.avg_risk !== undefined ? spot.avg_risk : 
            0;

          let parsedRisk = parseFloat(rawRisk);

          // Если риск в долях (например, 0.741), переводим в проценты (74.1%)
          if (!isNaN(parsedRisk) && parsedRisk > 0 && parsedRisk <= 1.0) {
            parsedRisk = parsedRisk * 100;
          }

          const riskDisplay = !isNaN(parsedRisk) ? parsedRisk.toFixed(1) : "0.0";

          return (
            <div 
              key={idx} 
              className="hotspot-item"
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "6px 10px",
                background: "rgba(239, 68, 68, 0.1)",
                borderLeft: "3px solid #ef4444",
                borderRadius: "4px",
                fontSize: "11.5px"
              }}
            >
              <span style={{ color: "#fca5a5", fontWeight: "500" }}>
                Hotspot #{idx + 1}
              </span>
              <span style={{ color: "#ffffff", fontWeight: "600" }}>
                Risk: {riskDisplay}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}