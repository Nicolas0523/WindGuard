import os
import ee

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
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

climate_cache = {}
RESOLUTION_KM = 10

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


@app.post("/analyze")
def analyze(data: AnalysisRequest):
    try:
        polygon = ee.Geometry.Polygon(data.geometry.coordinates)
        
        actual_start, actual_end, is_forecast = resolve_dates(
            data.start_date, data.end_date
        )
        grid_cells = prediction_grid(polygon, actual_start, actual_end, resolution_km=RESOLUTION_KM)

        if not grid_cells:
            return {"error": f"No data for {actual_start} → {actual_end}"}

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
    except Exception as e:
        print("\n!!! ПРОИЗОШЛА ОШИБКА В ANALYZE !!!")
        import traceback; print(traceback.format_exc())
        return {"error": str(e)}

@app.post("/analyze/short")
def forecast_short(data: AnalysisRequest):
    try:
        polygon = ee.Geometry.Polygon(data.geometry.coordinates)
        
        today        = datetime.now()
        actual_start = today.replace(year=today.year - 1).strftime("%Y-%m-%d")
        actual_end   = (today.replace(year=today.year - 1) + timedelta(days=30)).strftime("%Y-%m-%d")

    forecast_from = today.strftime("%Y-%m-%d")
    forecast_to   = (today + timedelta(days=10)).strftime("%Y-%m-%d")

        grid_cells = prediction_grid(polygon, actual_start, actual_end, resolution_km=RESOLUTION_KM)

        if not grid_cells:
            return {"error": f"No data for {actual_start} → {actual_end}"}

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
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {"error": str(e)}

@app.post("/analyze/climate")
def analyze_climate(data: AnalysisRequest):
    try:
        polygon   = ee.Geometry.Polygon(data.geometry.coordinates)
        cache_key = f"future_{str(data.geometry.coordinates)}_{data.start_date}"

        if cache_key in climate_cache:
            return climate_cache[cache_key]

        try:
            month = int(data.start_date.split("-")[1])
        except Exception:
            month = 6  

        grid_climate = prediction_future_grid(polygon, month=month, resolution_km=RESOLUTION_KM)

        if not grid_climate:
            return {"error": "Не удалось сгенерировать климатический прогноз для данного региона."}

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

    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {"error": str(e)}

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