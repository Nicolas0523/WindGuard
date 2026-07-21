from extract_features import extract_features, extract_features_grid, extract_future_features_grid
from data_loader import load_raw_data, load_raw_data_multi_year
from config import ml_model
from datetime import datetime


def prediction_val(polygon, start_date, end_date):

    raw_data = load_raw_data_multi_year(
        polygon,
        start_date,
        end_date
    )

    month = datetime.strptime(
        start_date,
        "%Y-%m-%d"
    ).month

    scaled_features, _ = extract_features(
        raw_data,
        polygon,
        month
    )

    result = ml_model.predict(scaled_features)[0]

    return float(result)


def prediction_grid(polygon, start_date, end_date, resolution_km=10):
    raw_data = load_raw_data_multi_year(polygon, start_date, end_date)
    month = datetime.strptime(start_date, "%Y-%m-%d").month

    scaled, coords_meta = extract_features_grid(raw_data, polygon, month, resolution_km)

    if len(scaled) == 0: return []

    preds = ml_model.predict(scaled)

    grid_results = []
    for i, (cell, risk) in enumerate(zip(coords_meta, preds)):
        grid_results.append({
            "lat": cell["lat"],
            "lon": cell["lon"],
            "risk": float(risk),
            "ndvi": float(scaled[i][0]), 
            "wind": float(scaled[i][1]),
            "temp": float(scaled[i][2]),
        })

    return grid_results


def prediction_future_grid(polygon, month, resolution_km=10):
    raw_data = load_raw_data_multi_year(polygon, "2025-06-01", "2025-08-31") 

    scaled, coords_meta = extract_future_features_grid(
        raw_data, polygon, month, resolution_km=resolution_km
    )

    if len(scaled) == 0:
        return []

    preds = ml_model.predict(scaled)

    grid_results = []
    for cell, risk in zip(coords_meta, preds):
        grid_results.append({
            "i": cell.get('i', 0),
            "j": cell.get('j', 0),
            "lat": cell["lat"],
            "lon": cell["lon"],
            "risk": float(risk),
            "step_deg": cell["step_deg"]  
        })

    return grid_results

def get_feature_importance():
    features = [
        "NDVI_now", "wind_mean", "wind_max", "wind_erosivity", "rain", "tempC", 
        "soil_moisture", "evaporation", "slope", "soil_type", "biome", "month", 
        "latitude", "longitude", "ndvi_wind_interaction", "aridity_index", 
        "is_dry_season", "ndvi_zscore", "ndvi_biome_anomaly"
    ]
    
    importances = ml_model.feature_importances_
    
    feature_data = [
        {"name": f, "value": float(i)} 
        for f, i in zip(features, importances)
    ]
    
    return sorted(feature_data, key=lambda x: x['value'], reverse=True)