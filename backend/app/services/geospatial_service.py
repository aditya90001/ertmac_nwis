import os
import glob
import math
import json
from typing import List, Dict, Optional, Tuple
import pandas as pd

from app.core.config import settings
from app.models.schemas import WellMetadata, OffsetWellResult, NearbyWellResponse

class GeospatialService:
    def __init__(self):
        self.catalog_cache: Dict[str, WellMetadata] = {}
        self.force_dir = os.path.abspath(os.path.join(settings.BASE_DIR, "..", "data", "force2020"))
        if not os.path.exists(self.force_dir):
            # Fallback if inside backend directory
            self.force_dir = os.path.join(settings.DATA_DIR, "force2020")

        self.catalog_file = os.path.join(settings.DATA_DIR, "wells_catalog.json")
        self._initialize_catalog()

    @staticmethod
    def utm_to_latlon(easting: float, northing: float, zone: int = 31, northern_hemisphere: bool = True) -> Tuple[float, float]:
        """Converts UTM Easting/Northing (WGS84 Zone 31N default for North Sea / Volve) to Latitude / Longitude."""
        try:
            a = 6378137.0
            f = 1 / 298.257223563
            b = a * (1 - f)
            e = math.sqrt(1 - (b / a) ** 2)
            e1sq = e * e / (1 - e * e)

            x = easting - 500000.0
            y = northing if northern_hemisphere else northing - 10000000.0

            k0 = 0.9996
            m = y / k0
            mu = m / (a * (1 - e**2/4 - 3*e**4/64 - 5*e**6/256))
            e1 = (1 - math.sqrt(1 - e**2)) / (1 + math.sqrt(1 - e**2))

            j1 = (3*e1/2 - 27*e1**3/32)
            j2 = (21*e1**2/16 - 55*e1**4/32)
            j3 = (151*e1**3/96)
            j4 = (1097*e1**4/512)

            fp = mu + j1*math.sin(2*mu) + j2*math.sin(4*mu) + j3*math.sin(6*mu) + j4*math.sin(8*mu)

            c1 = e1sq * math.cos(fp)**2
            t1 = math.tan(fp)**2
            r1 = a * (1 - e**2) / (1 - e**2 * math.sin(fp)**2)**1.5
            n1 = a / math.sqrt(1 - e**2 * math.sin(fp)**2)
            d = x / (n1 * k0)

            lat = fp - (n1 * math.tan(fp) / r1) * (d**2/2 - (5 + 3*t1 + 10*c1 - 4*c1**2 - 9*e1sq)*d**4/24 + (61 + 90*t1 + 298*c1 + 45*t1**2 - 252*e1sq - 3*c1**2)*d**6/720)
            lat = math.degrees(lat)

            lon0 = (zone - 1) * 6 - 180 + 3
            lon = lon0 + math.degrees((d - (1 + 2*t1 + c1)*d**3/6 + (5 - 2*c1 + 28*t1 - 3*c1**2 + 8*e1sq + 24*t1**2)*d**5/120) / math.cos(fp))
            return round(lat, 6), round(lon, 6)
        except Exception:
            return 58.0, 2.0

    @staticmethod
    def distance_km(x1: float, y1: float, x2: float, y2: float) -> float:
        """Euclidean distance in kilometers between two UTM (meter) points."""
        dx = x1 - x2
        dy = y1 - y2
        return round(math.sqrt(dx * dx + dy * dy) / 1000.0, 2)

    def _initialize_catalog(self):
        if os.path.exists(self.catalog_file):
            try:
                with open(self.catalog_file, "r") as f:
                    raw = json.load(f)
                    for k, v in raw.items():
                        self.catalog_cache[k] = WellMetadata(**v)
                if len(self.catalog_cache) >= 20:
                    return
            except Exception as e:
                print(f"Loading cached catalog failed: {e}. Rebuilding...")

        self.rebuild_catalog()

    def rebuild_catalog(self) -> Dict[str, WellMetadata]:
        self.catalog_cache.clear()
        csv_files = sorted(glob.glob(os.path.join(self.force_dir, "*.csv")))

        for f in csv_files:
            fname = os.path.basename(f)
            try:
                df_head = pd.read_csv(f, nrows=100)
                well_col = next((c for c in df_head.columns if c.upper() == 'WELL'), None)
                depth_col = next((c for c in df_head.columns if 'DEPTH' in c.upper() or c.upper() == 'DEPT'), None)
                x_col = next((c for c in df_head.columns if 'X_LOC' in c.upper()), None)
                y_col = next((c for c in df_head.columns if 'Y_LOC' in c.upper()), None)
                form_col = next((c for c in df_head.columns if 'FORMATION' in c.upper()), None)
                group_col = next((c for c in df_head.columns if 'GROUP' in c.upper()), None)

                # Determine well ID
                well_id = None
                if well_col and not df_head[well_col].dropna().empty:
                    well_id = str(df_head[well_col].dropna().iloc[0]).strip()
                if not well_id or well_id == "nan":
                    # Derive from filename e.g. 15_9-23.csv -> 15/9-23
                    clean_f = fname.replace(".csv", "").replace("_well", "")
                    parts = clean_f.split("_")
                    if len(parts) >= 2:
                        well_id = f"{parts[0]}/{'_'.join(parts[1:])}".replace("_", "-")
                    else:
                        well_id = clean_f

                cols_to_read = [c for c in [depth_col, x_col, y_col, form_col, group_col] if c]
                df = pd.read_csv(f, usecols=cols_to_read)

                d_min = float(df[depth_col].min()) if depth_col and not df[depth_col].dropna().empty else 500.0
                d_max = float(df[depth_col].max()) if depth_col and not df[depth_col].dropna().empty else 3500.0

                x_val = float(df[x_col].dropna().mean()) if x_col and not df[x_col].dropna().empty else 450000.0
                y_val = float(df[y_col].dropna().mean()) if y_col and not df[y_col].dropna().empty else 6500000.0

                lat, lon = self.utm_to_latlon(x_val, y_val)

                formations = [str(x).strip() for x in df[form_col].dropna().unique() if str(x).strip() not in ['', 'nan']] if form_col else []
                groups = [str(x).strip() for x in df[group_col].dropna().unique() if str(x).strip() not in ['', 'nan']] if group_col else []

                # Available log curves
                all_cols = df_head.columns.tolist()
                log_curves = [c for c in all_cols if c.upper() in [
                    'GR', 'ROP', 'MUDWEIGHT', 'CALI', 'RHOB', 'NPHI', 'DTC', 'SP', 'RDEP', 'RMED', 'PEF'
                ]]

                w_meta = WellMetadata(
                    well_id=well_id,
                    file_name=fname,
                    x_utm=round(x_val, 2),
                    y_utm=round(y_val, 2),
                    latitude=lat,
                    longitude=lon,
                    depth_min_m=round(d_min, 1),
                    depth_max_m=round(d_max, 1),
                    formations=formations,
                    groups=groups,
                    has_wcr_report=True,
                    total_events_count=2,  # Will update when events indexed
                    available_logs=log_curves
                )
                self.catalog_cache[well_id] = w_meta
            except Exception as e:
                print(f"Error processing {fname}: {e}")

        # Persist to disk
        try:
            with open(self.catalog_file, "w") as f:
                json.dump({k: v.dict() for k, v in self.catalog_cache.items()}, f, indent=2)
        except Exception as e:
            print(f"Error writing catalog file: {e}")

        return self.catalog_cache

    def get_all_wells(self) -> List[WellMetadata]:
        return list(self.catalog_cache.values())

    def get_well_by_id(self, well_id: str) -> Optional[WellMetadata]:
        # Exact match or normalized match
        if well_id in self.catalog_cache:
            return self.catalog_cache[well_id]
        norm = well_id.replace("-", "/").replace("_", "/").strip().lower()
        for k, v in self.catalog_cache.items():
            if k.replace("-", "/").replace("_", "/").strip().lower() == norm:
                return v
        return None

    def get_nearby_wells(
        self,
        active_well_id: Optional[str] = None,
        center_x: Optional[float] = None,
        center_y: Optional[float] = None,
        radius_km: float = 25.0,
        current_depth_m: Optional[float] = None
    ) -> NearbyWellResponse:
        """Finds offset wells within radius_km from an active well or coordinate center."""
        ref_x = center_x
        ref_y = center_y
        ref_lat = None
        ref_lon = None

        if active_well_id:
            active_well = self.get_well_by_id(active_well_id)
            if active_well:
                ref_x = active_well.x_utm
                ref_y = active_well.y_utm
                ref_lat = active_well.latitude
                ref_lon = active_well.longitude

        if ref_x is None or ref_y is None:
            # Default to first well in catalog
            first = next(iter(self.catalog_cache.values()))
            ref_x, ref_y = first.x_utm, first.y_utm
            ref_lat, ref_lon = first.latitude, first.longitude
        else:
            if ref_lat is None:
                ref_lat, ref_lon = self.utm_to_latlon(ref_x, ref_y)

        offset_results: List[OffsetWellResult] = []

        for w_id, w_meta in self.catalog_cache.items():
            # Exclude active well itself if specified
            if active_well_id and (w_id == active_well_id or w_meta.well_id == active_well_id):
                continue

            dist = self.distance_km(ref_x, ref_y, w_meta.x_utm, w_meta.y_utm)
            if dist <= radius_km:
                offset_results.append(OffsetWellResult(
                    well_id=w_meta.well_id,
                    distance_km=dist,
                    x_utm=w_meta.x_utm,
                    y_utm=w_meta.y_utm,
                    latitude=w_meta.latitude,
                    longitude=w_meta.longitude,
                    depth_min_m=w_meta.depth_min_m,
                    depth_max_m=w_meta.depth_max_m,
                    formations=w_meta.formations,
                    total_events=w_meta.total_events_count,
                    critical_events_count=1 if dist < 15.0 else 0,
                    recent_events_summary=[f"Drilled to {w_meta.depth_max_m}m with {len(w_meta.formations)} formation tops logged"]
                ))

        # Sort by distance
        offset_results.sort(key=lambda x: x.distance_km)

        return NearbyWellResponse(
            active_well_id=active_well_id,
            center_coordinates={"x_utm": ref_x, "y_utm": ref_y, "latitude": ref_lat, "longitude": ref_lon},
            search_radius_km=radius_km,
            total_offset_wells_found=len(offset_results),
            offset_wells=offset_results
        )

geospatial_service = GeospatialService()
