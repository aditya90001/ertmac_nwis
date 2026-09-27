import asyncio
import datetime
import random
from typing import AsyncGenerator, Dict, Any, Optional

from app.models.schemas import StreamFrame, RiskPredictionRequest
from app.services.risk_service import risk_service
from app.services.geospatial_service import geospatial_service

class SimulationService:
    def __init__(self):
        self.is_streaming = False

    async def generate_drilling_telemetry_stream(
        self,
        active_well_id: str = "15/9-23",
        start_depth_m: float = 1650.0,
        end_depth_m: float = 2450.0,
        rate_m_per_step: float = 2.5,
        interval_seconds: float = 1.0
    ) -> AsyncGenerator[StreamFrame, None]:
        """Simulates real-time eRTMAC / WITSML streaming sensor data with live predictive risk inference."""
        cur_depth = start_depth_m

        while cur_depth <= end_depth_m:
            # Physics-based synthetic sensor readings
            # Near 1690m (known loss interval in offset wells)
            near_loss = abs(cur_depth - 1695.0) < 35.0
            near_kick = abs(cur_depth - 2165.0) < 35.0
            near_stuck = abs(cur_depth - 2430.0) < 25.0

            if near_kick:
                rop = round(random.uniform(36.0, 48.0), 1)  # Drilling break
                flow_out = round(random.uniform(115.0, 130.0), 1)  # Pit gain
                mud_weight = 1.21
                spp = round(random.uniform(2100, 2300), 1)
                torque = round(random.uniform(11000, 13000), 1)
            elif near_loss:
                rop = round(random.uniform(16.0, 24.0), 1)
                flow_out = round(random.uniform(15.0, 45.0), 1)  # Severe mud loss
                mud_weight = 1.25
                spp = round(random.uniform(1700, 1950), 1)  # SPP drop
                torque = round(random.uniform(9000, 11500), 1)
            elif near_stuck:
                rop = round(random.uniform(4.0, 8.0), 1)
                flow_out = 98.0
                mud_weight = 1.28
                spp = round(random.uniform(2700, 3100), 1)  # SPP spike
                torque = round(random.uniform(19500, 24000), 1)  # High torque
            else:
                rop = round(random.uniform(14.0, 26.0), 1)
                flow_out = round(random.uniform(97.0, 102.0), 1)
                mud_weight = 1.22
                spp = round(random.uniform(2350, 2550), 1)
                torque = round(random.uniform(10500, 13500), 1)

            gr = round(random.uniform(50.0, 85.0), 1)
            flow_in = 680.0

            # Predict real-time risk
            pred_req = RiskPredictionRequest(
                active_well_id=active_well_id,
                current_depth_m=cur_depth,
                current_rop=rop,
                current_mudweight=mud_weight,
                current_caliper=8.5,
                current_gr=gr,
                current_spp=spp,
                current_torque=torque,
                offset_radius_km=25.0
            )

            risk_res = risk_service.predict_risk(pred_req)
            latest_alert = risk_res.proactive_alerts[0] if risk_res.proactive_alerts else None

            frame = StreamFrame(
                timestamp=datetime.datetime.utcnow().isoformat() + "Z",
                depth_m=round(cur_depth, 1),
                rop_m_hr=rop,
                mud_weight_sg=mud_weight,
                torque_ft_lbs=torque,
                spp_psi=spp,
                flow_in_gpm=flow_in,
                flow_out_pct=flow_out,
                gamma_ray_api=gr,
                formation=risk_res.formation,
                risk_level=risk_res.overall_risk_level,
                active_alerts_count=len(risk_res.proactive_alerts),
                latest_alert=latest_alert
            )

            yield frame
            cur_depth += rate_m_per_step
            await asyncio.sleep(interval_seconds)

simulation_service = SimulationService()
