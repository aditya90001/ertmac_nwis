import json
import asyncio
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.models.schemas import StreamFrame
from app.services.simulation_service import simulation_service

router = APIRouter(prefix="/stream", tags=["Real-Time eRTMAC Stream"])

@router.get("/active-well", summary="Real-time Server-Sent Events (SSE) live drilling telemetry and proactive risk stream")
async def stream_active_well(
    active_well_id: str = Query("15/9-23", description="Active well identifier"),
    start_depth_m: float = Query(1650.0, description="Bit start depth in meters"),
    end_depth_m: float = Query(2450.0, description="Bit target depth in meters"),
    step_m: float = Query(5.0, description="Depth advance per frame"),
    delay_sec: float = Query(1.0, description="Streaming interval per second")
):
    async def event_generator():
        stream = simulation_service.generate_drilling_telemetry_stream(
            active_well_id=active_well_id,
            start_depth_m=start_depth_m,
            end_depth_m=end_depth_m,
            rate_m_per_step=step_m,
            interval_seconds=delay_sec
        )
        async for frame in stream:
            payload = json.dumps(frame.model_dump())
            yield f"data: {payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/snapshot", response_model=StreamFrame, summary="Get single snapshot telemetry frame for active well")
async def get_stream_snapshot(
    active_well_id: str = Query("15/9-23", description="Active well identifier"),
    current_depth_m: float = Query(1690.0, description="Current bit depth in meters")
):
    stream = simulation_service.generate_drilling_telemetry_stream(
        active_well_id=active_well_id,
        start_depth_m=current_depth_m,
        end_depth_m=current_depth_m + 1.0,
        rate_m_per_step=1.0,
        interval_seconds=0.01
    )
    async for frame in stream:
        return frame
