import os

class Settings:
    PROJECT_NAME: str = "eRTMAC-NWIS (Nearby Wells Intelligence System)"
    PROJECT_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    DESCRIPTION: str = "AI-Powered Offset Well Knowledge & Decision Support Platform for Drilling Operations (SIH26121 - Oil India Limited)"

    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    FORCE2020_DIR: str = os.path.join(DATA_DIR, "force2020")
    PDF_DIR: str = os.path.join(DATA_DIR, "wcr_reports")
    MODELS_DIR: str = os.path.join(DATA_DIR, "models")
    CACHE_DIR: str = os.path.join(DATA_DIR, "cache")

    EVENTS_CSV: str = os.path.join(DATA_DIR, "extracted_well_events.csv")
    EVENTS_JSON: str = os.path.join(DATA_DIR, "extracted_well_events.json")
    WELLS_METADATA_JSON: str = os.path.join(DATA_DIR, "wells_catalog.json")

    DEFAULT_SEARCH_RADIUS_KM: float = 25.0
    PROACTIVE_LOOKAHEAD_METERS: float = 50.0  # Alert when bit is within 50m of offset hazard

    # Risk Thresholds
    RISK_THRESHOLD_LOW: float = 0.25
    RISK_THRESHOLD_MEDIUM: float = 0.50
    RISK_THRESHOLD_HIGH: float = 0.75
    RISK_THRESHOLD_CRITICAL: float = 0.85

settings = Settings()

# Ensure directories exist
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.PDF_DIR, exist_ok=True)
os.makedirs(settings.MODELS_DIR, exist_ok=True)
os.makedirs(settings.CACHE_DIR, exist_ok=True)
