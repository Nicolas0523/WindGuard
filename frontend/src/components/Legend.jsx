import React from "react";
import { RISK_COLORS } from "../utils/colors";

export default function Legend() {
  return (
    <div className="map-legend glass-panel">
      <h5 className="legend-title">Wind Erosion Risk</h5>
      <div className="legend-scale">
        <div className="legend-item">
          <span className="color-dot" style={{ backgroundColor: RISK_COLORS.high }}></span>
          <span>High (&gt; 60%)</span>
        </div>
        <div className="legend-item">
          <span className="color-dot" style={{ backgroundColor: RISK_COLORS.medium }}></span>
          <span>Medium (30% - 60%)</span>
        </div>
        <div className="legend-item">
          <span className="color-dot" style={{ backgroundColor: RISK_COLORS.low }}></span>
          <span>Low (&lt; 30%)</span>
        </div>
      </div>
    </div>
  );
}