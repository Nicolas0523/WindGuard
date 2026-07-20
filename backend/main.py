import os
import ee
import gc
import uuid
import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from aiogram.types import Update
from bot.bot_instance import bot, dp

from schemas import AnalysisRequest, ChatRequest
from assistant import generate_individual_response
from predictor import prediction_grid, prediction_future_grid, get_feature_importance
from grid import calculate_hotspots  
from gee_service import resolve_dates

try:
    service_account = os.getenv("GEE_SERVICE_ACCOUNT")
    private_key     = os.getenv("GEE_PRIVATE_KEY")
    credentials = ee.ServiceAccountCredentials(service_account, key_data=private_key)
    ee.Initialize(credentials)
except Exception:
    ee.Authenticate()
    ee.Initialize()

tasks_db = {}
climate_cache = {}

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_url:
        webhook_url = f"{render_url.rstrip('/')}/telegram/webhook"
        logging.info(f"Setting webhook to {webhook_url}")
        await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
    else:
        logging.warning("RENDER_EXTERNAL_URL is not set!")
    
    yield
    await bot.delete_webhook()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_adaptive_resolution(start_date: str, end_date: str) -> int:
    try:
        if not start_date or not end_date:
            return 10
        s = datetime.strptime(start_date, "%Y-%m-%d")
        e = datetime.strptime(end_date, "%Y-%m-%d")
        years = abs((e - s).days) / 365.0
        
        if years > 5:
            return 25  
        elif years > 2:
            return 15  
        return 10     
    except Exception:
        return 10


def run_heavy_prediction_sync(coordinates, start_date, end_date):
    try:
        resolution_km = get_adaptive_resolution(start_date, end_date)
        polygon = ee.Geometry.Polygon(coordinates)
        actual_start, actual_end, is_forecast = resolve_dates(start_date, end_date)
        
        grid_cells = prediction_grid(polygon, actual_start, actual_end, resolution_km=resolution_km)
        if not grid_cells:
            return {"error": f"No data for {actual_start} → {actual_end}"}

        avg_risk = sum(p["risk"] for p in grid_cells) / len(grid_cells)
        hotspots = calculate_hotspots(grid_cells, risk_threshold=0.7, min_size=3)

        return {
            "polygon": coordinates,
            "grid": grid_cells,
            "risk_score": round(avg_risk, 4),
            "hotspots": hotspots,
            "feature_importances": get_feature_importance(),
            "context": {
                "risk_score": round(avg_risk, 4),
                "start_date": actual_start,
                "end_date": actual_end,
                "forecast": is_forecast
            }
        }
    finally:
        gc.collect()


def run_short_forecast_sync(coordinates):
    try:
        polygon = ee.Geometry.Polygon(coordinates)
        today = datetime.now()
        actual_start = today.replace(year=today.year - 1).strftime("%Y-%m-%d")
        actual_end   = (today.replace(year=today.year - 1) + timedelta(days=30)).strftime("%Y-%m-%d")

        forecast_from = today.strftime("%Y-%m-%d")
        forecast_to   = (today + timedelta(days=10)).strftime("%Y-%m-%d")

        grid_cells = prediction_grid(polygon, actual_start, actual_end, resolution_km=10)
        if not grid_cells:
            return {"error": f"No data for {actual_start} → {actual_end}"}

        avg_risk = sum(p["risk"] for p in grid_cells) / len(grid_cells)
        hotspots = calculate_hotspots(grid_cells, risk_threshold=0.7, min_size=3)

        return {
            "polygon": coordinates,
            "grid": grid_cells, 
            "risk_score": round(avg_risk, 4),
            "hotspots": hotspots,
            "forecast_type": "10-day",
            "is_forecast": True,
            "period": f"{forecast_from} to {forecast_to}",
            "feature_importances": get_feature_importance(),
            "context": {
                "risk_score": round(avg_risk, 4),
                "start_date": actual_start,
                "end_date": actual_end,
            }
        }
    finally:
        gc.collect()


def run_climate_forecast_sync(coordinates, start_date):
    try:
        polygon = ee.Geometry.Polygon(coordinates)
        try:
            month = int(start_date.split("-")[1])
        except Exception:
            month = 6  

        grid_climate = prediction_future_grid(polygon, month=month, resolution_km=15)
        if not grid_climate:
            return {"error": "Не удалось сгенерировать климатический прогноз."}

        future_risk = sum(p["risk"] for p in grid_climate) / len(grid_climate)
        hotspots = calculate_hotspots(grid_climate, risk_threshold=0.7, min_size=3)

        return {
            "polygon": coordinates,
            "grid": grid_climate,
            "risk_score": round(future_risk, 4),
            "hotspots": hotspots,
            "scenario": "SSP5-8.5",
            "period": "2040-2050",
            "is_forecast": True,
            "feature_importances": get_feature_importance(),
            "context": {
                "risk_score": round(future_risk, 4),
                "scenario": "SSP5-8.5",
                "period": "2050",
            }
        }
    finally:
        gc.collect()


async def async_task_runner(task_id: str, func, *args):
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(process_pool, func, *args)
        
        if isinstance(result, dict) and "error" in result:
            tasks_db[task_id] = {"status": "error", "error": result["error"]}
        else:
            tasks_db[task_id] = {"status": "completed", "result": result}
    except Exception as e:
        tasks_db[task_id] = {"status": "error", "error": str(e)}


@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot=bot, update=update)
        return {"ok": True}
    except Exception as e:
        logging.error(f"Error handling Telegram update: {e}")
        return {"ok": False, "error": str(e)}

@app.get("/analyze/status/{task_id}")
async def check_task_status(task_id: str):
    task = tasks_db.get(task_id)
    if not task:
        return {"status": "not_found"}
    return task

@app.post("/analyze")
async def analyze_start(data: AnalysisRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {"status": "processing"}
    background_tasks.add_task(
        async_task_runner, task_id, run_heavy_prediction_sync, 
        data.geometry.coordinates, data.start_date, data.end_date
    )
    return {"task_id": task_id, "status": "processing"}

@app.post("/analyze/short")
async def forecast_short_start(data: AnalysisRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {"status": "processing"}
    background_tasks.add_task(
        async_task_runner, task_id, run_short_forecast_sync, 
        data.geometry.coordinates
    )
    return {"task_id": task_id, "status": "processing"}

@app.post("/analyze/climate")
async def analyze_climate_start(data: AnalysisRequest, background_tasks: BackgroundTasks):
    cache_key = f"future_{str(data.geometry.coordinates)}_{data.start_date}"
    if cache_key in climate_cache:
        return {"status": "completed", "result": climate_cache[cache_key]}

    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {"status": "processing"}
    background_tasks.add_task(
        async_task_runner, task_id, run_climate_forecast_sync, 
        data.geometry.coordinates, data.start_date
    )
    return {"task_id": task_id, "status": "processing"}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        ai_response = await asyncio.to_thread(
            generate_individual_response,
            user_message=req.message,
            data=req.analysis_data
        )
        return {"response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))