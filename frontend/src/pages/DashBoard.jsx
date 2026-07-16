import { useState } from "react";

import Navbar from "../components/Navbar.jsx";
import { ControlPanel } from "../components/Sidebar.jsx";
import RiskCard from "../components/RiskCard.jsx";
import HotspotList from "../components/HotspotList.jsx"; // Импортируем наш исправленный список хотспотов
import Assistant from "../components/Assistant.jsx";
import Legend from "../components/Legend.jsx"; 
import MapView from "../map/MapView";
import ExportPDF from "../components/ExportPDF"; // Импортируем кнопку экспорта PDF

import { useAnalysis } from "../hooks/useAnalysis";

import "../styles/dashboard.css";

export default function Dashboard() {
  const [polygon, setPolygon] = useState(null);
  const { analysis, loading, executeAnalysis } = useAnalysis();

  // Состояние для сохранения последнего ответа ИИ (для PDF отчета)
  const [lastAiResponse, setLastAiResponse] = useState(""); 

  return (
    <div className="app">
      <Navbar />

      <div className="dashboard">
        {/* ЛЕВАЯ ПАНЕЛЬ: Ассистент */}
        <div className="left-panel">
          <Assistant 
            analysis={analysis} 
            onNewResponse={(text) => setLastAiResponse(text)} // Передаем колбэк ответа ИИ
          />
        </div>

        {/* КАРТА (занимает центр экрана) */}
        <MapView 
          analysis={analysis} 
          setPolygon={setPolygon} 
        />

        {/* ПРАВАЯ ПАНЕЛЬ: Инструменты, результаты, легенда и PDF */}
        <div className="right-panel">
          <ControlPanel 
            onRunAnalysis={executeAnalysis} 
            loading={loading}
            polygon={polygon} 
          />
          
          {/* Если анализ выполнен и данные есть — рендерим результаты */}
          {analysis && (
            <>
              {/* 1. Карточка оценки риска (Risk Assessment 74.1%) */}
              <RiskCard analysis={analysis} />
              
              {/* 2. Список критических хотспотов с реальными рисками (СТРОГО ПОД КАРТОЧКОЙ РИСКА) */}
              <HotspotList analysis={analysis} />
              
              {/* 3. Кнопка PDF отчета */}
              <ExportPDF 
                analysis={analysis} 
                aiResponse={lastAiResponse} 
              />
            </>
          )}
          
          <Legend /> 
        </div>
      </div>
    </div>
  );
}