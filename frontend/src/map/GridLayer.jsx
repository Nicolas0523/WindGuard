import React from "react";
import { GeoJSON } from "react-leaflet";

export default function GridLayer({ gridData }) {
  if (!gridData) return null;

  const getGridStyle = (feature) => {
    const risk = feature.properties?.risk_score || 0;
    let color = "#10b981"; // Low Risk
    if (risk > 0.6) {
      color = "#ef4444"; // High Risk
    } else if (risk > 0.3) {
      color = "#f59e0b"; // Medium Risk
    }

    return {
      fillColor: color,
      weight: 1.5,
      opacity: 0.8,
      color: color,
      fillOpacity: 0.35,
    };
  };

  return (
    <GeoJSON
      key={JSON.stringify(gridData)}
      data={gridData}
      style={getGridStyle}
      onEachFeature={(feature, layer) => {
        const risk = (feature.properties?.risk_score * 100 || 0).toFixed(1);
        layer.bindPopup(`<strong>Wind Erosion Risk:</strong> ${risk}%`);
      }}
    />
  );
}