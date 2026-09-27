import sys, os
# Ensure backend/app is on PYTHONPATH for imports like `from app...`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import api_router
from app.services.geospatial_service import geospatial_service
from app.services.ingestion_service import ingestion_service
from app.services.risk_service import risk_service

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print(f"Starting {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}")
    print("=" * 60)
    wells = geospatial_service.get_all_wells()
    events = ingestion_service.get_all_events()
    print(f"Cataloged Wells: {len(wells)}")
    print(f"Indexed Drilling Incidents: {len(events)}")
    print(f"Risk Classifier Models: Ready")
    print("=" * 60)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include All API Endpoints
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.get("/", tags=["System"])
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "status": "ONLINE",
        "organization": "Oil India Limited (SIH26121)",
        "capabilities": [
            "Nearby-Well Geospatial & Offset Radius Search",
            "Cross-Well Stratigraphic & Petrophysical Log Correlation",
            "Institutional Knowledge Extraction from WCR/DDR PDFs",
            "Natural-Language & Parametric Historical Incident Search",
            "Real-Time Drilling Hazard Prediction (Mud Loss, Stuck Pipe, Kicks)",
            "Proactive Lookahead Risk Alerting with Offset Citations",
            "Pre-Spud Offset Intelligence Briefing Generator",
            "Simulated eRTMAC / WITSML Real-Time Telemetry Stream"
        ],
        "api_documentation": "/docs",
        "endpoints": {
            "wells": f"{settings.API_PREFIX}/wells",
            "nearby_wells": f"{settings.API_PREFIX}/wells/nearby",
            "cross_well_correlation": f"{settings.API_PREFIX}/correlate",
            "knowledge_search": f"{settings.API_PREFIX}/knowledge/search",
            "knowledge_events": f"{settings.API_PREFIX}/knowledge/events",
            "pre_spud_briefing": f"{settings.API_PREFIX}/knowledge/briefing",
            "risk_prediction": f"{settings.API_PREFIX}/risk/predict",
            "risk_heatmap": f"{settings.API_PREFIX}/risk/heatmap",
            "live_telemetry_stream": f"{settings.API_PREFIX}/stream/active-well"
        }
    }

@app.get("/health", tags=["System"])
def health_check():
    wells_count = len(geospatial_service.get_all_wells())
    events_count = len(ingestion_service.get_all_events())
    models_ready = bool(risk_service.models)

    return {
        "status": "HEALTHY",
        "timestamp": time.time(),
        "database": {
            "wells_loaded": wells_count,
            "drilling_events_indexed": events_count,
            "force2020_status": "ONLINE" if wells_count > 0 else "DEGRADED",
            "wcr_pdf_status": "ONLINE" if events_count > 0 else "DEGRADED"
        },
        "ml_inference": {
            "risk_classifiers": "ONLINE" if models_ready else "OFFLINE",
            "models": list(risk_service.models.keys())
        }
    }
