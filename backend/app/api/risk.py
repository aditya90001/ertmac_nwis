from typing import List, Dict, Any
from fastapi import APIRouter, Query

from app.models.schemas import RiskPredictionRequest, RiskPredictionResponse
from app.services.risk_service import risk_service

router = APIRouter(prefix="/risk", tags=["Predictive Risk & Alerts"])

@router.post("/predict", response_model=RiskPredictionResponse, summary="Predict real-time drilling hazard probabilities and proactive alerts")
def predict_drilling_risk(req: RiskPredictionRequest):
    return risk_service.predict_risk(req)

@router.get("/heatmap", response_model=List[Dict[str, Any]], summary="Get field-wide formation and depth risk heatmap")
def get_risk_heatmap(
    radius_km: float = Query(30.0, description="Offset radius to evaluate"),
    depth_step_m: float = Query(250.0, description="Depth resolution slice in meters")
):
    return risk_service.get_risk_heatmap(radius_km=radius_km, depth_step_m=depth_step_m)
