from fastapi import APIRouter
from app.api.wells import router as wells_router
from app.api.correlation import router as correlation_router
from app.api.knowledge import router as knowledge_router
from app.api.risk import router as risk_router
from app.api.stream import router as stream_router

api_router = APIRouter()
api_router.include_router(wells_router)
api_router.include_router(correlation_router)
api_router.include_router(knowledge_router)
api_router.include_router(risk_router)
api_router.include_router(stream_router)
