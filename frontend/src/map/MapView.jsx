import React from "react";

import { MapContainer, TileLayer, Rectangle, FeatureGroup } from "react-leaflet";

import { EditControl } from "react-leaflet-draw";



import "leaflet/dist/leaflet.css";

import "leaflet-draw/dist/leaflet.draw.css";



/**

 * Высококонтрастная 5-шаговая цветовая палитра.

 * Интерполирует цвета: Зеленый -> Салатовый -> Желтый -> Оранжевый -> Красный.

 */

const getHighContrastColor = (value) => {

  const t = Math.max(0, Math.min(1, value));



  let r, g, b;



  if (t < 0.25) {

    // [0.0 - 0.25]: Зеленый (16, 185, 129) -> Салатовый (132, 204, 22)

    const localT = t / 0.25;

    r = Math.round(16 + (132 - 16) * localT);

    g = Math.round(185 + (204 - 185) * localT);

    b = Math.round(129 + (22 - 129) * localT);

  } else if (t < 0.5) {

    // [0.25 - 0.5]: Салатовый (132, 204, 22) -> Желтый (234, 179, 8)

    const localT = (t - 0.25) / 0.25;

    r = Math.round(132 + (234 - 132) * localT);

    g = Math.round(204 + (179 - 204) * localT);

    b = Math.round(22 + (8 - 22) * localT);

  } else if (t < 0.75) {

    // [0.5 - 0.75]: Желтый (234, 179, 8) -> Оранжевый (249, 115, 22)

    const localT = (t - 0.5) / 0.25;

    r = Math.round(234 + (249 - 234) * localT);

    g = Math.round(179 + (115 - 179) * localT);

    b = Math.round(8 + (22 - 8) * localT);

  } else {

    // [0.75 - 1.0]: Оранжевый (249, 115, 22) -> Красный (239, 68, 68)

    const localT = (t - 0.75) / 0.25;

    r = Math.round(249 + (239 - 249) * localT);

    g = Math.round(115 + (68 - 115) * localT);

    b = Math.round(22 + (68 - 22) * localT);

  }



  return `rgb(${r}, ${g}, ${b})`;

};



export default function MapView({ analysis, setPolygon }) {

 

  const _onCreate = (e) => {

    const { layerType, layer } = e;

    if (layerType === "polygon") {

      const latlngs = layer.getLatLngs()[0];

      const formattedCoords = latlngs.map((ln) => [ln.lat, ln.lng]);

      setPolygon(formattedCoords);

    }

  };



  const _onDeleted = () => {

    setPolygon(null);

  };



  // --- ДИНАМИЧЕСКОЕ КОНТРАСТИРОВАНИЕ (MIN-MAX STRETCHING) ---

  let minRisk = 0;

  let maxRisk = 1;



  if (analysis && analysis.grid && analysis.grid.length > 0) {

    const risks = analysis.grid

      .map((cell) => cell.risk)

      .filter((r) => r !== undefined && !isNaN(r));



    if (risks.length > 0) {

      minRisk = Math.min(...risks);

      maxRisk = Math.max(...risks);

    }

  }



  return (

    <div style={{ width: "100%", height: "100%", position: "relative" }}>

      <MapContainer

        center={[48.0196, 66.9237]}

        zoom={5}

        style={{ height: "100%", width: "100%" }}

        zoomControl={true}

      >

        <TileLayer

          attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'

          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"

        />



        <FeatureGroup>

          <EditControl

            position="topleft"

            onCreated={_onCreate}

            onDeleted={_onDeleted}

            draw={{

              rectangle: false,

              circle: false,

              circlemarker: false,

              polyline: false,

              marker: false,

              polygon: {

                allowIntersection: false,

                drawError: { color: "#ef4444", message: "Lines cannot intersect!" },

                shapeOptions: { color: "#3b82f6", weight: 3, fillOpacity: 0.1 }

              }

            }}

          />

        </FeatureGroup>



        {/* ================= ОТРИСОВКА СЕТКИ ================= */}

        {analysis && analysis.grid && analysis.grid.map((cell, index) => {

          if (cell.lat === undefined || cell.lon === undefined) return null;



          const step = cell.step_deg || (10 / 111.0);

          const halfStep = step / 2;



          const bounds = [

            [cell.lat - halfStep, cell.lon - halfStep],

            [cell.lat + halfStep, cell.lon + halfStep]

          ];



          // Вычисляем контрастное (нормализованное) значение риска для этой ячейки

          const range = maxRisk - minRisk;

          const normalizedRisk = range > 0.01

            ? (cell.risk - minRisk) / range

            : cell.risk; // Предотвращаем деление на ноль



          return (

            <Rectangle

              key={`cell-${index}`}

              bounds={bounds}

              pathOptions={{

                color: "transparent",

                fillColor: getHighContrastColor(normalizedRisk), // Передаем контрастное значение

                fillOpacity: 0.75,

              }}

            />

          );

        })}

      </MapContainer>

    </div>

  );

}