import React from "react";

export default function RiskCard({ analysis }) {
  if (!analysis) return null;

  // Форматируем процент риска эрозии
  const riskPercent = (analysis.risk_score * 100).toFixed(1);

  // Функция для определения текстового статуса и класса цвета
  const getRiskStatus = (score) => {
    if (score > 0.6) return { text: "High Risk", className: "risk-high" };
    if (score >= 0.3) return { text: "Medium Risk", className: "risk-medium" };
    return { text: "Low Risk", className: "risk-low" };
  };

  const status = getRiskStatus(analysis.risk_score);

  return (
    <div className="risk-card glass-panel" style={{ marginBottom: "20px", padding: "16px" }}>
      <div className="risk-header" style={{ marginBottom: "12px" }}>
        <span 
          className="risk-title" 
          style={{ 
            fontSize: "11px", 
            fontWeight: "600", 
            color: "#94a3b8", 
            letterSpacing: "1px" 
          }}
        >
          RISK ASSESSMENT
        </span>
      </div>
      
      <div 
        className="risk-value-container" 
        style={{ 
          display: "flex", 
          justifyContent: "space-between", 
          alignItems: "baseline" 
        }}
      >
        <span 
          className={`risk-level ${status.className}`}
          style={{ 
            fontSize: "18px", 
            fontWeight: "700", 
            color: status.className === "risk-high" ? "#ef4444" : status.className === "risk-medium" ? "#f59e0b" : "#10b981"
          }}
        >
          {status.text}
        </span>
        <span className="risk-percentage" style={{ fontSize: "24px", fontWeight: "800", color: "#ffffff" }}>
          {riskPercent}%
        </span>
      </div>

      {/* Красивая уменьшенная строчка Grid Cells с отступом */}
      <div 
        className="grid-cells-info" 
        style={{ 
          marginTop: "14px", 
          paddingTop: "10px", 
          borderTop: "1px solid rgba(255, 255, 255, 0.05)",
          fontSize: "10.5px", 
          color: "#64748b", 
          letterSpacing: "0.3px",
          fontWeight: "400"
        }}
      >
        Grid Cells: {analysis.grid?.length || 0} units (10x10 km)
      </div>
    </div>
  );
}