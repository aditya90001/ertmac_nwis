from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class WellMetadata(BaseModel):
    well_id: str
    file_name: str
    x_utm: float
    y_utm: float
    latitude: float
    longitude: float
    depth_min_m: float
    depth_max_m: float
    formations: List[str] = []
    groups: List[str] = []
    has_wcr_report: bool = True
    total_events_count: int = 0
    available_logs: List[str] = []

class NearbyWellQuery(BaseModel):
    active_well_id: Optional[str] = None
    center_x: Optional[float] = None
    center_y: Optional[float] = None
    radius_km: float = 25.0
    current_depth_m: Optional[float] = None

class OffsetWellResult(BaseModel):
    well_id: str
    distance_km: float
    x_utm: float
    y_utm: float
    latitude: float
    longitude: float
    depth_min_m: float
    depth_max_m: float
    formations: List[str] = []
    total_events: int = 0
    critical_events_count: int = 0
    recent_events_summary: List[str] = []

class NearbyWellResponse(BaseModel):
    active_well_id: Optional[str] = None
    center_coordinates: Dict[str, float]
    search_radius_km: float
    total_offset_wells_found: int
    offset_wells: List[OffsetWellResult]

class HistoricalEvent(BaseModel):
    event_id: str
    well_id: str
    report_id: str
    page_number: int
    depth_start_m: float
    depth_end_m: float
    formation: str
    event_type: str
    severity: str
    npt_hours: float
    mitigation_action: str
    verbatim_excerpt: str
    file_path: Optional[str] = None

class KnowledgeSearchQuery(BaseModel):
    query: Optional[str] = None
    well_id: Optional[str] = None
    formation: Optional[str] = None
    event_type: Optional[str] = None
    depth_min: Optional[float] = None
    depth_max: Optional[float] = None
    severity: Optional[str] = None
    limit: int = 20

class KnowledgeSearchResult(BaseModel):
    total_matches: int
    query_applied: Dict[str, Any]
    results: List[HistoricalEvent]
    ai_summary: Optional[str] = None

class CrossWellCorrelationRequest(BaseModel):
    active_well_id: str
    offset_well_ids: Optional[List[str]] = None
    radius_km: float = 25.0
    depth_min_m: Optional[float] = None
    depth_max_m: Optional[float] = None
    log_curves: List[str] = ["GR", "ROP", "MUDWEIGHT", "CALI", "RHOB"]

class WellLogTrack(BaseModel):
    depth: List[float]
    values: List[Optional[float]]
    unit: str

class WellCorrelationTrack(BaseModel):
    well_id: str
    distance_km: float
    formation_tops: List[Dict[str, Any]]
    logs: Dict[str, WellLogTrack]
    historical_events: List[Dict[str, Any]]

class CrossWellCorrelationResponse(BaseModel):
    active_well_id: str
    depth_range: Dict[str, float]
    wells: List[WellCorrelationTrack]
    stratigraphic_correlation_matrix: List[Dict[str, Any]]

class RiskPredictionRequest(BaseModel):
    active_well_id: Optional[str] = "15/9-23"
    current_depth_m: float
    current_formation: Optional[str] = None
    current_rop: Optional[float] = 18.5
    current_mudweight: Optional[float] = 1.25
    current_caliper: Optional[float] = 8.5
    current_gr: Optional[float] = 65.0
    current_spp: Optional[float] = 2400.0
    current_torque: Optional[float] = 12000.0
    offset_radius_km: float = 25.0

class ProactiveAlert(BaseModel):
    alert_id: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    hazard_type: str
    lookahead_distance_m: float
    target_depth_m: float
    formation: str
    trigger_reason: str
    historical_offset_well: str
    historical_event_excerpt: str
    citation_source: str
    recommended_mitigation: str

class RiskPredictionResponse(BaseModel):
    current_depth_m: float
    formation: str
    overall_risk_score: float
    overall_risk_level: str
    hazard_probabilities: Dict[str, float]
    feature_contributions: Dict[str, float]
    proactive_alerts: List[ProactiveAlert]
    field_recommendations: List[str]

class PreSpudBriefingRequest(BaseModel):
    planned_well_name: str
    x_utm: float
    y_utm: float
    planned_td_m: float
    radius_km: float = 30.0

class PreSpudBriefingResponse(BaseModel):
    planned_well_name: str
    coordinates: Dict[str, float]
    radius_km: float
    offset_wells_analyzed: int
    offset_well_names: List[str]
    formation_progression: List[Dict[str, Any]]
    top_drilling_hazards: List[Dict[str, Any]]
    casing_point_recommendations: List[Dict[str, Any]]
    recommended_mud_program: List[Dict[str, Any]]
    lessons_learned_summary: List[str]
    high_risk_depth_intervals: List[Dict[str, Any]]

class StreamFrame(BaseModel):
    timestamp: str
    depth_m: float
    rop_m_hr: float
    mud_weight_sg: float
    torque_ft_lbs: float
    spp_psi: float
    flow_in_gpm: float
    flow_out_pct: float
    gamma_ray_api: float
    formation: str
    risk_level: str
    active_alerts_count: int
    latest_alert: Optional[ProactiveAlert] = None
