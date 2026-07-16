import React, { useRef } from "react";
import { FeatureGroup } from "react-leaflet";
import { EditControl } from "react-leaflet-draw";

export default function PolygonLayer({ setPolygon }) {
  const featureGroupRef = useRef(null);

  const handleCreated = (e) => {
    const { layerType, layer } = e;
    if (layerType === "polygon") {
      const container = featureGroupRef.current;
      if (container) {
        container.eachLayer((existingLayer) => {
          if (existingLayer !== layer) {
            container.removeLayer(existingLayer);
          }
        });
      }
      setPolygon(layer.toGeoJSON());
    }
  };

  const handleEdited = (e) => {
    e.layers.eachLayer((layer) => {
      setPolygon(layer.toGeoJSON());
    });
  };

  const handleDeleted = () => {
    setPolygon(null);
  };

  return (
    <FeatureGroup ref={featureGroupRef}>
      <EditControl
        position="topleft"
        onCreated={handleCreated}
        onEdited={handleEdited}
        onDeleted={handleDeleted}
        draw={{
          polygon: {
            allowIntersection: false,
            drawError: {
              color: "#ef4444",
              message: "<strong>Error:</strong> Polygons cannot intersect!",
            },
            shapeOptions: {
              color: "#3b82f6",
              fillColor: "#3b82f6",
              fillOpacity: 0.15,
              weight: 3,
            },
          },
          rectangle: false,
          circle: false,
          polyline: false,
          marker: false,
          circlemarker: false,
        }}
      />
    </FeatureGroup>
  );
}