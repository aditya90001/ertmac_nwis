from fastapi import APIRouter
from app.models.schemas import CrossWellCorrelationRequest, CrossWellCorrelationResponse
from app.services.correlation_service import correlation_service

router = APIRouter(prefix="/correlate", tags=["Cross-Well Correlation"])

@router.post("", response_model=CrossWellCorrelationResponse, summary="Correlate drilling curves, stratigraphy, and NPT events across offset wells")
def correlate_wells(req: CrossWellCorrelationRequest):
    return correlation_service.correlate_wells(req)
