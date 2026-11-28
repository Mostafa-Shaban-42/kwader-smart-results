"""Single source of truth for school years. Dynamic 5-year system."""
from backend.core.config import YEARS_CONFIG

def get_enabled_years() -> list[dict]:
    return [{"id": k, **v} for k, v in sorted(YEARS_CONFIG.items(), key=lambda x: x[1]["order"]) if v["enabled"]]

def is_year_enabled(year_id: str) -> bool:
    return YEARS_CONFIG.get(year_id, {}).get("enabled", False)

def get_year_label(year_id: str) -> str:
    return YEARS_CONFIG.get(year_id, {}).get("label", year_id)