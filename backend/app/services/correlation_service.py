import os
import glob
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from app.core.config import settings
from app.models.schemas import (
    CrossWellCorrelationRequest, CrossWellCorrelationResponse,
    WellCorrelationTrack, WellLogTrack
)
from app.services.geospatial_service import geospatial_service
from app.services.knowledge_service import knowledge_service

class CorrelationService:
    def __init__(self):
        self.force_dir = os.path.abspath(os.path.join(settings.BASE_DIR, "..", "data", "force2020"))
        if not os.path.exists(self.force_dir):
            self.force_dir = os.path.join(settings.DATA_DIR, "force2020")

    def correlate_wells(self, req: CrossWellCorrelationRequest) -> CrossWellCorrelationResponse:
        active_meta = geospatial_service.get_well_by_id(req.active_well_id)
        if not active_meta:
            # Fallback to first available well
            all_w = geospatial_service.get_all_wells()
            active_meta = all_w[0] if all_w else None

        # Determine target offset wells
        target_offset_ids = req.offset_well_ids or []
        if not target_offset_ids:
            nearby = geospatial_service.get_nearby_wells(
                active_well_id=active_meta.well_id,
                radius_km=req.radius_km
            )
            target_offset_ids = [w.well_id for w in nearby.offset_wells[:4]]

        wells_to_correlate = [active_meta.well_id] + [wid for wid in target_offset_ids if wid != active_meta.well_id]

        depth_min = req.depth_min_m or active_meta.depth_min_m
        depth_max = req.depth_max_m or min(active_meta.depth_max_m, depth_min + 1200.0)

        correlation_tracks: List[WellCorrelationTrack] = []
        all_formations_matrix: List[Dict[str, Any]] = []

        for wid in wells_to_correlate:
            w_meta = geospatial_service.get_well_by_id(wid)
            if not w_meta:
                continue

            dist = 0.0 if wid == active_meta.well_id else geospatial_service.distance_km(
                active_meta.x_utm, active_meta.y_utm, w_meta.x_utm, w_meta.y_utm
            )

            # Load well log data
            log_data, formation_tops = self._load_well_curves(
                w_meta.file_name,
                depth_min,
                depth_max,
                req.log_curves
            )

            # Load historical events for this well in this depth window
            events = knowledge_service.get_events_for_depth_window(
                target_depth_m=depth_min,
                lookahead_m=(depth_max - depth_min),
                offset_wells=[wid]
            )

            event_markers = [
                {
                    "event_id": e.event_id,
                    "depth_start": e.depth_start_m,
                    "depth_end": e.depth_end_m,
                    "event_type": e.event_type,
                    "severity": e.severity,
                    "mitigation": e.mitigation_action
                }
                for e in events
            ]

            correlation_tracks.append(WellCorrelationTrack(
                well_id=wid,
                distance_km=dist,
                formation_tops=formation_tops,
                logs=log_data,
                historical_events=event_markers
            ))

        return CrossWellCorrelationResponse(
            active_well_id=active_meta.well_id,
            depth_range={"min_m": depth_min, "max_m": depth_max},
            wells=correlation_tracks,
            stratigraphic_correlation_matrix=all_formations_matrix
        )

    def _load_well_curves(
        self,
        file_name: str,
        depth_min: float,
        depth_max: float,
        curve_names: List[str]
    ) -> (Dict[str, WellLogTrack], List[Dict[str, Any]]):
        fpath = os.path.join(self.force_dir, file_name)
        if not os.path.exists(fpath):
            return {}, []

        try:
            # Read header
            head = pd.read_csv(fpath, nrows=2)
            cols = head.columns.tolist()
            depth_col = next((c for c in cols if 'DEPTH' in c.upper() or c.upper() == 'DEPT'), None)
            form_col = next((c for c in cols if 'FORMATION' in c.upper()), None)

            selected_cols = [depth_col]
            matched_curves = {}
            for target_curve in curve_names:
                for c in cols:
                    if c.upper() == target_curve.upper():
                        selected_cols.append(c)
                        matched_curves[target_curve.upper()] = c
                        break

            if form_col:
                selected_cols.append(form_col)

            df = pd.read_csv(fpath, usecols=[c for c in selected_cols if c])

            # Filter depth
            df = df[(df[depth_col] >= depth_min) & (df[depth_col] <= depth_max)]
            if df.empty:
                # Fallback to any available depth interval in well
                df = pd.read_csv(fpath, usecols=[c for c in selected_cols if c]).dropna(subset=[depth_col]).head(200)

            # Decimate to ~100 points for fast transmission
            step = max(1, len(df) // 100)
            df_sampled = df.iloc[::step].copy()

            depths = [round(float(x), 1) for x in df_sampled[depth_col].tolist()]

            # Extract formation tops
            formation_tops = []
            if form_col and form_col in df.columns:
                prev_form = None
                for idx, row in df.iterrows():
                    cur_form = str(row[form_col]).strip()
                    if cur_form and cur_form != 'nan' and cur_form != prev_form:
                        formation_tops.append({
                            "formation": cur_form,
                            "top_depth_m": round(float(row[depth_col]), 1)
                        })
                        prev_form = cur_form

            # Build log tracks
            units = {
                "GR": "gAPI",
                "ROP": "m/hr",
                "MUDWEIGHT": "SG",
                "CALI": "in",
                "RHOB": "g/cm3",
                "NPHI": "m3/m3",
                "DTC": "us/ft",
                "SP": "mV"
            }

            tracks = {}
            for curve_key, col_name in matched_curves.items():
                vals = []
                for v in df_sampled[col_name]:
                    if pd.isna(v) or np.isnan(v):
                        vals.append(None)
                    else:
                        vals.append(round(float(v), 2))

                tracks[curve_key] = WellLogTrack(
                    depth=depths,
                    values=vals,
                    unit=units.get(curve_key, "")
                )

            return tracks, formation_tops

        except Exception as e:
            print(f"Error loading curves from {file_name}: {e}")
            return {}, []

correlation_service = CorrelationService()
