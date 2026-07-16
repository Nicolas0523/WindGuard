from pydantic import BaseModel
from typing import List, Dict, Literal, Optional, Any

class Geometry(BaseModel):
    coordinates: List[List[List[float]]]
    type: Literal["Polygon"]

class AnalysisRequest(BaseModel):
    geometry: Geometry
    start_date: str
    end_date: str
    
class AnalysisResult(BaseModel):
    predictions: float
    feature_importances: dict

class ChatRequest(BaseModel):
    message: str
    analysis_data: Optional[Dict[str, Any]] = None