import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse

from app.core.config import settings
from app.models.schemas import (
    HistoricalEvent, KnowledgeSearchQuery, KnowledgeSearchResult,
    PreSpudBriefingRequest, PreSpudBriefingResponse
)
from app.services.knowledge_service import knowledge_service
from app.services.ingestion_service import ingestion_service
from app.services.briefing_service import briefing_service

router = APIRouter(prefix="/knowledge", tags=["Institutional Knowledge & NLP Search"])

@router.get("/events", response_model=List[HistoricalEvent], summary="List all extracted historical drilling events")
def list_events(
    well_id: Optional[str] = Query(None, description="Filter by well name"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    formation: Optional[str] = Query(None, description="Filter by formation")
):
    events = ingestion_service.get_all_events()
    if well_id:
        events = [e for e in events if well_id.lower() in e.well_id.lower()]
    if event_type:
        events = [e for e in events if event_type.lower() in e.event_type.lower()]
    if formation:
        events = [e for e in events if formation.lower() in e.formation.lower()]
    return events

@router.post("/search", response_model=KnowledgeSearchResult, summary="Natural-language or parametric search for drilling events with citations")
def search_knowledge(query: KnowledgeSearchQuery):
    return knowledge_service.search_events(query)

@router.get("/pdf/{report_id}", summary="Download or view source WCR PDF report")
def get_pdf(report_id: str):
    clean_id = report_id.replace(".pdf", "")
    pdf_name = f"{clean_id}.pdf"
    file_path = os.path.join(settings.BASE_DIR, "data", "wcr_reports", pdf_name)
    if not os.path.exists(file_path):
        # Try finding partial name
        wcr_dir = os.path.join(settings.BASE_DIR, "data", "wcr_reports")
        for f in os.listdir(wcr_dir):
            if clean_id in f:
                file_path = os.path.join(wcr_dir, f)
                break

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"PDF report '{report_id}' not found")

    return FileResponse(file_path, media_type="application/pdf", filename=os.path.basename(file_path))

@router.post("/upload-wcr", response_model=List[HistoricalEvent], summary="Upload and automatically parse new WCR PDF into institutional knowledge")
async def upload_wcr(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    save_path = os.path.join(settings.BASE_DIR, "data", "wcr_reports", file.filename)
    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    new_events = ingestion_service.add_uploaded_pdf(save_path)
    return new_events

@router.post("/briefing", response_model=PreSpudBriefingResponse, summary="Generate executive pre-spud offset well briefing")
def get_pre_spud_briefing(req: PreSpudBriefingRequest):
    return briefing_service.generate_pre_spud_briefing(req)
