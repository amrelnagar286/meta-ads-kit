"""
Profile Manager — Multi-business/brand profile system with JSON persistence.
Supports CRUD, import/export, per-profile credentials, favorites, and recent activity.
"""
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

log = logging.getLogger(__name__)

PROFILES_DIR = Path(__file__).parent.parent / "profiles"
PROFILES_INDEX = PROFILES_DIR / "profiles.json"

# Brand color presets for quick selection
BRAND_COLORS = {
    "Blue": "#0078D4",
    "Red": "#D13438",
    "Green": "#107C10",
    "Orange": "#FF8C00",
    "Purple": "#881798",
    "Teal": "#00B7C3",
    "Pink": "#E3008C",
    "Yellow": "#FFB900",
    "Navy": "#002050",
    "Gray": "#605E5C",
}


def _ensure_dirs():
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    if not PROFILES_INDEX.exists():
        PROFILES_INDEX.write_text(json.dumps({
            "active_profile": None,
            "profiles": {},
            "recent_activity": [],
            "favorites": [],
        }, indent=2), encoding="utf-8")


def _load_index() -> dict:
    _ensure_dirs()
    return json.loads(PROFILES_INDEX.read_text(encoding="utf-8"))


def _save_index(data: dict):
    _ensure_dirs()
    PROFILES_INDEX.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _log_activity(index: dict, action: str, profile_name: str, details: str = ""):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "profile": profile_name,
        "details": details,
    }
    index.setdefault("recent_activity", []).insert(0, entry)
    index["recent_activity"] = index["recent_activity"][:100]


def create_profile(
    name: str,
    access_token: str = "",
    ad_account_id: str = "",
    business_name: str = "",
    brand_color: str = "#0078D4",
    notes: str = "",
    industry: str = "",
    currency: str = "USD",
    timezone: str = "America/New_York",
    monthly_budget: float = 0.0,
    benchmarks: Optional[dict] = None,
    tags: Optional[List[str]] = None,
) -> dict:
    """Create a new business/brand profile."""
    index = _load_index()
    profile_id = str(uuid4())[:8]

    profile = {
        "id": profile_id,
        "name": name,
        "business_name": business_name or name,
        "access_token": access_token,
        "ad_account_id": ad_account_id,
        "brand_color": brand_color,
        "notes": notes,
        "industry": industry,
        "currency": currency,
        "timezone": timezone,
        "monthly_budget": monthly_budget,
        "benchmarks": benchmarks or {
            "target_ctr": 2.0,
            "max_frequency": 3.5,
            "target_roas": 3.0,
            "max_cpa": 50.0,
            "bleeder_ctr": 1.0,
            "bleeder_spend": 10.0,
        },
        "tags": tags or [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "last_connected": None,
        "total_extractions": 0,
        "favorite_pages": [],
        "custom_kpi_formulas": [],
        "workspace": {
            "last_page": None,
            "last_date_preset": "last_30d",
            "last_levels": ["ad"],
            "last_breakdowns": ["none"],
        },
    }

    index["profiles"][profile_id] = profile
    if not index.get("active_profile"):
        index["active_profile"] = profile_id
    _log_activity(index, "created", name)
    _save_index(index)
    log.info("Profile created: %s (%s)", name, profile_id)
    return profile


def update_profile(profile_id: str, **kwargs) -> Optional[dict]:
    """Update an existing profile."""
    index = _load_index()
    if profile_id not in index["profiles"]:
        return None
    profile = index["profiles"][profile_id]
    for k, v in kwargs.items():
        if k in profile:
            profile[k] = v
    profile["updated_at"] = datetime.now().isoformat()
    _log_activity(index, "updated", profile["name"], f"Fields: {', '.join(kwargs.keys())}")
    _save_index(index)
    return profile


def delete_profile(profile_id: str) -> bool:
    """Delete a profile by ID."""
    index = _load_index()
    if profile_id not in index["profiles"]:
        return False
    name = index["profiles"][profile_id]["name"]
    del index["profiles"][profile_id]
    if index.get("active_profile") == profile_id:
        remaining = list(index["profiles"].keys())
        index["active_profile"] = remaining[0] if remaining else None
    index["favorites"] = [f for f in index.get("favorites", []) if f != profile_id]
    _log_activity(index, "deleted", name)
    _save_index(index)
    return True


def get_profile(profile_id: str) -> Optional[dict]:
    """Get a profile by ID."""
    index = _load_index()
    return index["profiles"].get(profile_id)


def get_all_profiles() -> Dict[str, dict]:
    """Get all profiles."""
    index = _load_index()
    return index["profiles"]


def get_active_profile() -> Optional[dict]:
    """Get the currently active profile."""
    index = _load_index()
    active_id = index.get("active_profile")
    if active_id and active_id in index["profiles"]:
        return index["profiles"][active_id]
    return None


def get_active_profile_id() -> Optional[str]:
    """Get the currently active profile ID."""
    index = _load_index()
    return index.get("active_profile")


def set_active_profile(profile_id: str) -> bool:
    """Switch to a different profile."""
    index = _load_index()
    if profile_id not in index["profiles"]:
        return False
    index["active_profile"] = profile_id
    name = index["profiles"][profile_id]["name"]
    _log_activity(index, "switched", name)
    _save_index(index)
    return True


def duplicate_profile(profile_id: str, new_name: str = "") -> Optional[dict]:
    """Duplicate an existing profile (without credentials)."""
    index = _load_index()
    original = index["profiles"].get(profile_id)
    if not original:
        return None
    new_profile = create_profile(
        name=new_name or f"{original['name']} (Copy)",
        business_name=original.get("business_name", ""),
        brand_color=original.get("brand_color", "#0078D4"),
        notes=original.get("notes", ""),
        industry=original.get("industry", ""),
        currency=original.get("currency", "USD"),
        timezone=original.get("timezone", "America/New_York"),
        monthly_budget=original.get("monthly_budget", 0.0),
        benchmarks=original.get("benchmarks"),
        tags=original.get("tags", []),
    )
    return new_profile


def toggle_favorite(profile_id: str) -> bool:
    """Toggle a profile as favorite."""
    index = _load_index()
    if profile_id not in index["profiles"]:
        return False
    favorites = index.get("favorites", [])
    if profile_id in favorites:
        favorites.remove(profile_id)
    else:
        favorites.append(profile_id)
    index["favorites"] = favorites
    _save_index(index)
    return True


def is_favorite(profile_id: str) -> bool:
    """Check if a profile is favorited."""
    index = _load_index()
    return profile_id in index.get("favorites", [])


def get_favorites() -> List[dict]:
    """Get all favorite profiles."""
    index = _load_index()
    favorites = index.get("favorites", [])
    return [index["profiles"][pid] for pid in favorites if pid in index["profiles"]]


def export_profiles(profile_ids: Optional[List[str]] = None) -> str:
    """Export profiles to a JSON string (credentials masked)."""
    index = _load_index()
    profiles_to_export = {}
    ids = profile_ids or list(index["profiles"].keys())
    for pid in ids:
        if pid in index["profiles"]:
            p = dict(index["profiles"][pid])
            p["access_token"] = ""
            profiles_to_export[pid] = p
    return json.dumps({
        "exported_at": datetime.now().isoformat(),
        "version": "1.0",
        "profiles": profiles_to_export,
    }, indent=2, default=str)


def import_profiles(data: str, overwrite: bool = False) -> List[str]:
    """Import profiles from a JSON string. Returns list of imported profile names."""
    index = _load_index()
    imported_data = json.loads(data)
    profiles = imported_data.get("profiles", {})
    imported_names = []
    for pid, profile in profiles.items():
        if pid in index["profiles"] and not overwrite:
            profile["id"] = str(uuid4())[:8]
            profile["name"] = f"{profile['name']} (Imported)"
            pid = profile["id"]
        profile["updated_at"] = datetime.now().isoformat()
        profile["access_token"] = ""
        index["profiles"][pid] = profile
        imported_names.append(profile["name"])
        _log_activity(index, "imported", profile["name"])
    if not index.get("active_profile") and index["profiles"]:
        index["active_profile"] = next(iter(index["profiles"]))
    _save_index(index)
    return imported_names


def record_connection(profile_id: str):
    """Record that a profile was successfully connected."""
    index = _load_index()
    if profile_id in index["profiles"]:
        index["profiles"][profile_id]["last_connected"] = datetime.now().isoformat()
        _save_index(index)


def record_extraction(profile_id: str):
    """Record that an extraction was run for a profile."""
    index = _load_index()
    if profile_id in index["profiles"]:
        index["profiles"][profile_id]["total_extractions"] = \
            index["profiles"][profile_id].get("total_extractions", 0) + 1
        _save_index(index)


def save_workspace(profile_id: str, **kwargs):
    """Save workspace state for a profile (last page, date preset, etc.)."""
    index = _load_index()
    if profile_id in index["profiles"]:
        ws = index["profiles"][profile_id].setdefault("workspace", {})
        ws.update(kwargs)
        _save_index(index)


def get_recent_activity(limit: int = 20) -> List[dict]:
    """Get recent activity across all profiles."""
    index = _load_index()
    return index.get("recent_activity", [])[:limit]


def get_profile_stats() -> dict:
    """Get aggregate stats across all profiles."""
    index = _load_index()
    profiles = index["profiles"]
    total = len(profiles)
    configured = sum(1 for p in profiles.values() if p.get("access_token") and p.get("ad_account_id"))
    total_extractions = sum(p.get("total_extractions", 0) for p in profiles.values())
    industries = list({p.get("industry", "") for p in profiles.values() if p.get("industry")})
    return {
        "total_profiles": total,
        "configured": configured,
        "total_extractions": total_extractions,
        "industries": industries,
        "favorites_count": len(index.get("favorites", [])),
    }


def add_custom_kpi(profile_id: str, name: str, formula: str, unit: str = "") -> bool:
    """Add a custom KPI formula to a profile."""
    index = _load_index()
    if profile_id not in index["profiles"]:
        return False
    formulas = index["profiles"][profile_id].setdefault("custom_kpi_formulas", [])
    formulas.append({
        "name": name,
        "formula": formula,
        "unit": unit,
        "created_at": datetime.now().isoformat(),
    })
    _save_index(index)
    return True


def remove_custom_kpi(profile_id: str, kpi_name: str) -> bool:
    """Remove a custom KPI formula from a profile."""
    index = _load_index()
    if profile_id not in index["profiles"]:
        return False
    formulas = index["profiles"][profile_id].get("custom_kpi_formulas", [])
    index["profiles"][profile_id]["custom_kpi_formulas"] = [
        f for f in formulas if f["name"] != kpi_name
    ]
    _save_index(index)
    return True
