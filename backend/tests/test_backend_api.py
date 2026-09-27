import os
import sys
import pytest
from fastapi.testclient import TestClient

# Put backend root on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from app.main import app

client = TestClient(app)

def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ONLINE"
    assert "capabilities" in data
    assert "endpoints" in data

def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["database"]["wells_loaded"] >= 20
    assert data["database"]["drilling_events_indexed"] >= 30
    assert data["ml_inference"]["risk_classifiers"] == "ONLINE"

def test_list_wells():
    res = client.get("/api/wells")
    assert res.status_code == 200
    wells = res.json()
    assert len(wells) >= 20
    well_ids = [w["well_id"] for w in wells]
    assert any("15/9-23" in wid or "15_9-23" in wid for wid in well_ids)

def test_get_specific_well():
    res = client.get("/api/wells/15/9-23")
    assert res.status_code == 200
    data = res.json()
    assert data["well_id"] == "15/9-23"
    assert data["x_utm"] > 400000
    assert data["y_utm"] > 6000000
    assert len(data["formations"]) > 0

def test_nearby_wells_radius_search():
    # Search around 15/9-23 within 25 km
    payload = {
        "active_well_id": "15/9-23",
        "radius_km": 25.0
    }
    res = client.post("/api/wells/nearby", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["search_radius_km"] == 25.0
    assert data["total_offset_wells_found"] >= 2
    offset_names = [w["well_id"] for w in data["offset_wells"]]
    # 15/9-14 and 16/7-6 are both within ~11 km of 15/9-23
    assert any("15/9-14" in w for w in offset_names)
    assert any("16/7-6" in w for w in offset_names)
    # Check that distances are under 25 km and sorted
    distances = [w["distance_km"] for w in data["offset_wells"]]
    assert distances == sorted(distances)
    assert all(d <= 25.0 for d in distances)

def test_cross_well_correlation():
    payload = {
        "active_well_id": "15/9-23",
        "radius_km": 25.0,
        "log_curves": ["GR", "ROP", "MUDWEIGHT", "CALI"],
        "depth_min_m": 1600.0,
        "depth_max_m": 2500.0
    }
    res = client.post("/api/correlate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["active_well_id"] == "15/9-23"
    assert len(data["wells"]) >= 2
    for track in data["wells"]:
        assert "logs" in track
        assert "formation_tops" in track
        assert "historical_events" in track

def test_knowledge_events_listing():
    res = client.get("/api/knowledge/events")
    assert res.status_code == 200
    events = res.json()
    assert len(events) >= 30
    assert all("event_type" in e for e in events)
    assert all("mitigation_action" in e for e in events)
    assert all("verbatim_excerpt" in e for e in events)

def test_knowledge_natural_language_search():
    # Natural language query: "lost circulation mud loss in Hordaland around 1700m"
    payload = {
        "query": "lost circulation mud loss in Hordaland around 1700m",
        "limit": 5
    }
    res = client.post("/api/knowledge/search", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_matches"] > 0
    assert len(data["results"]) > 0
    first = data["results"][0]
    assert "loss" in first["event_type"].lower() or "hordaland" in first["formation"].lower()
    assert len(first["mitigation_action"]) > 10
    assert data["ai_summary"] is not None

def test_predict_drilling_risk():
    # Normal drilling depth
    payload = {
        "active_well_id": "15/9-23",
        "current_depth_m": 2140.0,  # 10m lookahead to offset well 15/9-14 kick at 2150m
        "current_rop": 35.0,
        "current_mudweight": 1.25,
        "current_caliper": 8.5,
        "current_gr": 65.0,
        "current_spp": 1900.0,
        "current_torque": 11000.0,
        "offset_radius_km": 25.0
    }
    res = client.post("/api/risk/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "hazard_probabilities" in data
    assert "mud_loss_risk" in data["hazard_probabilities"]
    assert "stuck_pipe_risk" in data["hazard_probabilities"]
    assert "kick_risk" in data["hazard_probabilities"]
    assert data["overall_risk_score"] > 0.0
    # Proactive alert should be triggered because depth is within lookahead window of offset hazard
    assert len(data["proactive_alerts"]) > 0
    first_alert = data["proactive_alerts"][0]
    assert first_alert["historical_offset_well"] is not None
    assert first_alert["recommended_mitigation"] is not None
    assert "citation_source" in first_alert

def test_risk_heatmap():
    res = client.get("/api/risk/heatmap?radius_km=30&depth_step_m=250")
    assert res.status_code == 200
    heatmap = res.json()
    assert len(heatmap) > 5
    assert all("depth_interval_m" in item for item in heatmap)
    assert all("risk_density" in item for item in heatmap)
    assert all("representative_formation" in item for item in heatmap)

def test_pre_spud_briefing():
    payload = {
        "planned_well_name": "OIL-ASSAM-EXPLORATORY-01",
        "x_utm": 433919.0,
        "y_utm": 6459992.0,
        "planned_td_m": 3500.0,
        "radius_km": 30.0
    }
    res = client.post("/api/knowledge/briefing", json=payload)
    assert res.status_code == 200
    briefing = res.json()
    assert briefing["planned_well_name"] == "OIL-ASSAM-EXPLORATORY-01"
    assert briefing["offset_wells_analyzed"] >= 2
    assert len(briefing["top_drilling_hazards"]) > 0
    assert len(briefing["casing_point_recommendations"]) > 0
    assert len(briefing["recommended_mud_program"]) > 0
    assert len(briefing["lessons_learned_summary"]) > 0

def test_stream_snapshot():
    res = client.get("/api/stream/snapshot?active_well_id=15/9-23&current_depth_m=1690")
    assert res.status_code == 200
    frame = res.json()
    assert frame["depth_m"] == 1690.0
    assert "rop_m_hr" in frame
    assert "mud_weight_sg" in frame
    assert "risk_level" in frame

if __name__ == "__main__":
    pytest.main(["-v", __file__])
