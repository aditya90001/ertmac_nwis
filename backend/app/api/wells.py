from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import WellMetadata, NearbyWellQuery, NearbyWellResponse
from app.services.geospatial_service import geospatial_service

router = APIRouter(prefix="/wells", tags=["Wells & Geospatial"])

@router.get("", response_model=List[WellMetadata], summary="List all cataloged wells with geospatial coordinates")
def list_wells():
    return geospatial_service.get_all_wells()

@router.get("/{well_id:path}", response_model=WellMetadata, summary="Get technical metadata for a specific well")
def get_well(well_id: str):
    well = geospatial_service.get_well_by_id(well_id)
    if not well:
        raise HTTPException(status_code=404, detail=f"Well '{well_id}' not found in catalog")
    return well

@router.post("/nearby", response_model=NearbyWellResponse, summary="Find offset wells within user-defined radius")
def find_nearby_wells(query: NearbyWellQuery):
    return geospatial_service.get_nearby_wells(
        active_well_id=query.active_well_id,
        center_x=query.center_x,
        center_y=query.center_y,
        radius_km=query.radius_km,
        current_depth_m=query.current_depth_m
    )
