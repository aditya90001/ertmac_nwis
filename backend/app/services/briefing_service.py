from typing import Dict, Any, List
from app.models.schemas import PreSpudBriefingRequest, PreSpudBriefingResponse
from app.services.geospatial_service import geospatial_service
from app.services.knowledge_service import knowledge_service
from app.services.ingestion_service import ingestion_service

class BriefingService:
    def __init__(self):
        pass

    def generate_pre_spud_briefing(self, req: PreSpudBriefingRequest) -> PreSpudBriefingResponse:
        # Find offset wells within radius
        nearby_res = geospatial_service.get_nearby_wells(
            center_x=req.x_utm,
            center_y=req.y_utm,
            radius_km=req.radius_km
        )

        offset_wells = nearby_res.offset_wells
        offset_ids = [w.well_id for w in offset_wells]

        # Fetch all historical events for these offset wells
        all_events = ingestion_service.get_all_events()
        events = [e for e in all_events if e.well_id in offset_ids]

        # Top Drilling Hazards
        hazard_counts = {}
        for ev in events:
            hazard_counts[ev.event_type] = hazard_counts.get(ev.event_type, 0) + 1

        top_hazards = [
            {
                "hazard_name": k,
                "historical_occurrences": v,
                "typical_severity": "HIGH" if "loss" in k.lower() or "stuck" in k.lower() else "CRITICAL",
                "risk_rating": "High" if v >= 2 else "Medium"
            }
            for k, v in sorted(hazard_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        # Formation progression
        progression = [
            {"formation": "NORDLAND GP", "depth_interval": "0m - 1,000m", "lithology": "Unconsolidated sands and clays", "hazard_level": "LOW"},
            {"formation": "HORDALAND GP", "depth_interval": "1,000m - 1,850m", "lithology": "Reactive swelling claystones", "hazard_level": "HIGH (Tight hole / pack-off)"},
            {"formation": "ROGALAND GP / BALDER FM", "depth_interval": "1,850m - 2,400m", "lithology": "Tuffaceous shales & turbidite sands", "hazard_level": "HIGH (Gas influx / kicks)"},
            {"formation": "CHALK GP / EKOFISK FM", "depth_interval": "2,400m - 2,850m", "lithology": "Micro-fractured hard chalk", "hazard_level": "CRITICAL (Severe mud losses)"},
            {"formation": "VIKING GP / BRENT GP", "depth_interval": "2,850m - TD", "lithology": "Interbedded sandstone / siltstone", "hazard_level": "HIGH (Differential sticking)"}
        ]

        # Casing point recommendations
        casing_points = [
            {"section": "36\" Hole / 30\" Conductor", "recommended_shoe_m": 350.0, "justification": "Anchor structural seabed casing above shallow water flow sand."},
            {"section": "26\" Hole / 20\" Surface Casing", "recommended_shoe_m": 1050.0, "justification": "Isolate high water flow sands prior to entering reactive Hordaland claystones."},
            {"section": "17-1/2\" Hole / 13-3/8\" Intermediate", "recommended_shoe_m": 2200.0, "justification": "Case off swelling Hordaland shales before encountering overpressured Rogaland sands."},
            {"section": "12-1/4\" Hole / 9-5/8\" Production", "recommended_shoe_m": 2850.0, "justification": "Isolate fractured Chalk Group losses before drilling hydrocarbon reservoir."}
        ]

        # Recommended mud program
        mud_prog = [
            {"section": "0 - 1,050m", "mud_system": "Seawater / Bentonite Spud Mud", "density_sg": "1.05 - 1.12 SG", "primary_control": "Cuttings carrying capacity"},
            {"section": "1,050m - 2,200m", "mud_system": "KCl / Glycol Water Based Mud", "density_sg": "1.18 - 1.25 SG", "primary_control": "Clay swelling inhibition (> 6% KCl)"},
            {"section": "2,200m - TD", "mud_system": "Low Toxicity Oil Based Mud (SOBM)", "density_sg": "1.28 - 1.36 SG", "primary_control": "Bridging filtration control & lubricity"}
        ]

        # Lessons learned
        lessons = [
            "In Hordaland formation, maintain continuous rotation during connections to prevent reactive shale packing off around BHA.",
            "Pre-treat active mud pits with 20 ppb medium calcium carbonate prior to penetrating Chalk Group top at ~2,480m to arrest lost circulation.",
            "Keep trip speeds below 14 m/min across depleted reservoir sandstones to eliminate surge-induced formation fracturing.",
            "Maintain barite inventory of minimum 100 MT on deck prior to drilling Rogaland formation transition zone."
        ]

        # High risk depth intervals
        high_risk_intervals = [
            {"depth_range_m": "1,680m - 1,750m", "formation": "HORDALAND GP", "risk": "Lost Circulation", "historical_wells_affected": ["15/9-23", "25/11-24"]},
            {"depth_range_m": "2,150m - 2,220m", "formation": "ROGALAND GP / HEIMDAL FM", "risk": "Well Kick / Influx", "historical_wells_affected": ["15/9-14", "25/10-10"]},
            {"depth_range_m": "2,480m - 2,550m", "formation": "CHALK GP", "risk": "Lost Circulation (Fractured)", "historical_wells_affected": ["16/7-6", "34/3-3 A"]},
            {"depth_range_m": "3,010m - 3,110m", "formation": "BRENT GP", "risk": "Differential Sticking & Losses", "historical_wells_affected": ["35/9-8"]}
        ]

        return PreSpudBriefingResponse(
            planned_well_name=req.planned_well_name,
            coordinates={"x_utm": req.x_utm, "y_utm": req.y_utm},
            radius_km=req.radius_km,
            offset_wells_analyzed=len(offset_wells),
            offset_well_names=offset_ids,
            formation_progression=progression,
            top_drilling_hazards=top_hazards,
            casing_point_recommendations=casing_points,
            recommended_mud_program=mud_prog,
            lessons_learned_summary=lessons,
            high_risk_depth_intervals=high_risk_intervals
        )

briefing_service = BriefingService()
