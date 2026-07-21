import os
import ee
import asyncio
import uuid 

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from datetime import datetime, timedelta

from aiogram.types import Update
from bot.bot_instance import bot, dp

from schemas import AnalysisRequest, ChatRequest
from assistant import generate_individual_response
from predictor import prediction_grid, prediction_future_grid, get_feature_importance
from grid import calculate_hotspots 
from gee_service import resolve_dates, gee_retry

try:
    service_account = os.getenv("GEE_SERVICE_ACCOUNT")
    private_key     = os.getenv("GEE_PRIVATE_KEY")
    credentials = ee.ServiceAccountCredentials(service_account, key_data=private_key)
    ee.Initialize(credentials)
except Exception:
    ee.Authenticate()
    ee.Initialize()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

climate_cache = {}
jobs = {}

GEE_TIMEOUT_SECONDS = 80  

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)
    return {"ok": True}

@app.on_event("startup")
async def set_bot_webhook():
    render_url = "https://windguard-1.onrender.com"
    await bot.set_webhook(url=f"{render_url}/telegram/webhook")


def get_adaptive_resolution(polygon: ee.Geometry) -> int:
    try:
        # Площадь в кв. км
        area_sq_km = polygon.area().getInfo() / 1e6
        if area_sq_km > 100000:
            return 40  
        elif area_sq_km > 30000:
            return 25  
        elif area_sq_km > 5000:
            return 15  
        return 10      
    except Exception:
        return 15


# --- HISTORICAL ANALYSIS ---
@app.post("/analyze")
async def analyze(data: AnalysisRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing"}
    background_tasks.add_task(_run_analyze, job_id, data)
    return {"job_id": job_id, "status": "processing"}

async def _run_analyze(job_id: str, data: AnalysisRequest):
    try:
        result = await asyncio.wait_for(
            run_in_threadpool(_analyze_sync, data),
            timeout=GEE_TIMEOUT_SECONDS
        )
        jobs[job_id] = {"status": "done", **result}
    except asyncio.TimeoutError:
        print(f"[TIMEOUT] Job {job_id} exceeded GEE_TIMEOUT_SECONDS")
        jobs[job_id] = {
            "status": "error", 
            "error": "Анализ превысил лимит времени (80 сек). Выберите меньшую область на карте."
        }
    except Exception as e:
        import traceback; print(traceback.format_exc())
        jobs[job_id] = {"status": "error", "error": str(e)}

def _analyze_sync(data: AnalysisRequest):
    polygon = ee.Geometry.Polygon(data.geometry.coordinates)
    resolution = get_adaptive_resolution(polygon)
        
    actual_start, actual_end, is_forecast = resolve_dates(data.start_date, data.end_date)
    grid_cells = prediction_grid(polygon, actual_start, actual_end, resolution_km=resolution)

    if not grid_cells:
        return {"error": f"Нет данных для периода {actual_start} → {actual_end}"}

    avg_risk = sum(p["risk"] for p in grid_cells) / len(grid_cells)
    hotspots = calculate_hotspots(grid_cells, risk_threshold=0.7, min_size=3)

    return {
        "polygon":    data.geometry.coordinates,
        "grid":       grid_cells,  
        "risk_score": round(avg_risk, 4),
        "hotspots":   hotspots,  
        "feature_importances": get_feature_importance(),
        "context": {
            "risk_score": round(avg_risk, 4),
            "start_date": actual_start,
            "end_date":   actual_end,
            "forecast":   is_forecast
        }
    }


# --- 10-DAY FORECAST ---
@app.post("/analyze/short")
async def forecast_short(data: AnalysisRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing"}
    background_tasks.add_task(_run_short_forecast, job_id, data)
    return {"job_id": job_id, "status": "processing"}

async def _run_short_forecast(job_id: str, data: AnalysisRequest):
    try:
        result = await asyncio.wait_for(
            run_in_threadpool(short_forecast_sync, data),
            timeout=GEE_TIMEOUT_SECONDS
        )
        jobs[job_id] = {"status": "done", **result}
    except asyncio.TimeoutError:
        print(f"[TIMEOUT] Job {job_id} exceeded GEE_TIMEOUT_SECONDS")
        jobs[job_id] = {
            "status": "error", 
            "error": "Анализ превысил лимит времени (80 сек). Выберите меньшую область на карте."
        }
    except Exception as e:
        import traceback; print(traceback.format_exc())
        jobs[job_id] = {"status": "error", "error": str(e)}

def short_forecast_sync(data: AnalysisRequest):
    polygon = ee.Geometry.Polygon(data.geometry.coordinates)
    resolution = get_adaptive_resolution(polygon)
        
    today        = datetime.now()
    actual_start = today.replace(year=today.year - 1).strftime("%Y-%m-%d")
    actual_end   = (today.replace(year=today.year - 1) + timedelta(days=30)).strftime("%Y-%m-%d")

    forecast_from = today.strftime("%Y-%m-%d")
    forecast_to   = (today + timedelta(days=10)).strftime("%Y-%m-%d")

    grid_cells = prediction_grid(polygon, actual_start, actual_end, resolution_km=resolution)

    if not grid_cells:
        return {"error": f"Нет данных для периода {actual_start} → {actual_end}"}

    avg_risk = sum(p["risk"] for p in grid_cells) / len(grid_cells)
    hotspots = calculate_hotspots(grid_cells, risk_threshold=0.7, min_size=3)

    return {
        "polygon":       data.geometry.coordinates,
        "grid":          grid_cells, 
        "risk_score":    round(avg_risk, 4),
        "hotspots":      hotspots,
        "forecast_type": "10-day",
        "is_forecast":   True,
        "note":          "Forecast based on same period last year",
        "period":        f"{forecast_from} to {forecast_to}",
        "feature_importances": get_feature_importance(),
        "context": {
            "risk_score":    round(avg_risk, 4),
            "start_date":    actual_start,
            "end_date":      actual_end,
            "forecast_from": forecast_from,
            "forecast_to":   forecast_to
        }
    }


# --- 2040-2050 CLIMATE PREDICTION ---
@app.post("/analyze/climate")
async def forecast_climate(data: AnalysisRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing"}
    background_tasks.add_task(_run_climate_forecast, job_id, data)
    return {"job_id": job_id, "status": "processing"}

async def _run_climate_forecast(job_id: str, data: AnalysisRequest):
    try:
        result = await asyncio.wait_for(
            run_in_threadpool(_climate_forecast_sync, data),
            timeout=GEE_TIMEOUT_SECONDS
        )
        jobs[job_id] = {"status": "done", **result}
    except asyncio.TimeoutError:
        print(f"[TIMEOUT] Job {job_id} exceeded GEE_TIMEOUT_SECONDS")
        jobs[job_id] = {
            "status": "error", 
            "error": "Анализ превысил лимит времени (80 сек). Выберите меньшую область на карте."
        }
    except Exception as e:
        import traceback; print(traceback.format_exc())
        jobs[job_id] = {"status": "error", "error": str(e)}

def _climate_forecast_sync(data: AnalysisRequest):
    polygon   = ee.Geometry.Polygon(data.geometry.coordinates)
    cache_key = f"future_{str(data.geometry.coordinates)}_{data.start_date}"

    if cache_key in climate_cache:
        return climate_cache[cache_key]

    try:
        month = int(data.start_date.split("-")[1])
    except Exception:
        month = 6  

    resolution = get_adaptive_resolution(polygon)
    grid_climate = prediction_future_grid(polygon, month=month, resolution_km=resolution)

    if not grid_climate:
        return {"error": "Failed to generate climate forecast for this region."}

    future_risk = sum(p["risk"] for p in grid_climate) / len(grid_climate)
    hotspots = calculate_hotspots(grid_climate, risk_threshold=0.7, min_size=3)

    result = {
        "polygon":     data.geometry.coordinates,
        "grid":        grid_climate,
        "risk_score":  round(future_risk, 4),
        "hotspots":    hotspots,
        "scenario":    "SSP5-8.5",
        "period":      "2040-2050",
        "is_forecast": True,
        "feature_importances": get_feature_importance(),
        "context": {
            "risk_score": round(future_risk, 4),
            "scenario":   "SSP5-8.5 (worst case)",
            "period":     "2050",
            "hotspots_found": len(hotspots)
        }
    }
        
    climate_cache[cache_key] = result
    return result


@app.get("/analyze/status/{job_id}")
async def get_status(job_id: str):
    if not job_id or job_id == "undefined":
        raise HTTPException(status_code=400, detail="Invalid job_id provided")

    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        ai_response = generate_individual_response(
            user_message=req.message,
            data=req.analysis_data
        )
        return {"response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))