import ee
import os
import joblib
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

SCRIPT_DIR  = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

SCALER_PATH   = PROJECT_ROOT / "scaler_v3.pkl"
MODEL_PATH    = PROJECT_ROOT / "xgb_model_v3.pkl"
FEATURES_PATH = PROJECT_ROOT / "features_v3.pkl"


ndvi_stats = joblib.load(SCRIPT_DIR / "ndvi_stats.pkl")
scaler   = joblib.load(SCALER_PATH)
ml_model = joblib.load(MODEL_PATH)
features = joblib.load(FEATURES_PATH)

# GEE инициализация
GEE_INITIALIZED = False

try:
    service_account = os.getenv("GEE_SERVICE_ACCOUNT")
    private_key     = os.getenv("GEE_PRIVATE_KEY")

    if service_account and private_key:
        credentials = ee.ServiceAccountCredentials(
            service_account, key_data=private_key
        )
        ee.Initialize(credentials)
        GEE_INITIALIZED = True
    else:
        pass

except Exception as e:
    print(f"GEE init failed: {e}")