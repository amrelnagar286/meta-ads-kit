"""
Multi-Source Data Importer -- CSV, JSON, Excel, Google Sheets (public links).
Auto-detects column types, handles Meta dashboard output format,
and provides schema preview before import.
"""
import io
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

import pandas as pd
import requests

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# COLUMN TYPE DETECTION
# ---------------------------------------------------------------------------

NUMERIC_PATTERNS = re.compile(
    r"^(spend|impressions|clicks|reach|frequency|cpm|cpc|ctr|cpl|cpa|roas|"
    r"conversions|purchases|revenue|cost|budget|amount|value|rate|ratio|"
    r"views|leads|adds_to_cart|initiated_checkouts|outbound_clicks|"
    r"link_clicks|landing_page_views|video_.*|action_.*|conversion_.*|"
    r"purchase_.*|unique_.*|total_.*|post_.*|estimated_.*|quality_.*|"
    r"engagement_.*|social_.*|canvas_.*|instant_.*|catalog_.*)",
    re.IGNORECASE,
)

DATE_PATTERNS = re.compile(
    r"^(date|date_start|date_stop|day|month|year|created|updated|"
    r"timestamp|time|period|week|quarter)$",
    re.IGNORECASE,
)

ID_PATTERNS = re.compile(
    r"^(.*_id|id|account_id|campaign_id|adset_id|ad_id|order_id|"
    r"customer_id|product_id|sku|code|reference)$",
    re.IGNORECASE,
)


def detect_column_types(df: pd.DataFrame) -> Dict[str, str]:
    """Detect column types: numeric, date, id, text."""
    types = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if DATE_PATTERNS.match(col_lower):
            types[col] = "date"
        elif ID_PATTERNS.match(col_lower):
            types[col] = "id"
        elif NUMERIC_PATTERNS.match(col_lower):
            types[col] = "numeric"
        elif df[col].dtype in ("int64", "float64"):
            types[col] = "numeric"
        else:
            try:
                pd.to_numeric(df[col], errors="raise")
                types[col] = "numeric"
            except (ValueError, TypeError):
                try:
                    pd.to_datetime(df[col], errors="raise", format="mixed")
                    types[col] = "date"
                except (ValueError, TypeError):
                    types[col] = "text"
    return types


def coerce_column_types(df: pd.DataFrame, type_map: Dict[str, str]) -> pd.DataFrame:
    """Coerce columns to the specified types."""
    result = df.copy()
    for col, dtype in type_map.items():
        if col not in result.columns:
            continue
        if dtype == "numeric":
            result[col] = pd.to_numeric(result[col], errors="coerce").fillna(0)
        elif dtype == "date":
            result[col] = pd.to_datetime(result[col], errors="coerce", format="mixed")
        elif dtype == "id":
            result[col] = result[col].astype(str).str.strip()
    return result


# ---------------------------------------------------------------------------
# FILE IMPORTERS
# ---------------------------------------------------------------------------

def import_csv(file_or_path, encoding: str = "utf-8-sig") -> pd.DataFrame:
    """Import a CSV file or file-like object."""
    try:
        df = pd.read_csv(file_or_path, encoding=encoding)
    except UnicodeDecodeError:
        if hasattr(file_or_path, "seek"):
            file_or_path.seek(0)
        df = pd.read_csv(file_or_path, encoding="latin-1")
    return df


def import_excel(file_or_path, sheet_name: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """Import an Excel file. Returns dict of {sheet_name: DataFrame}."""
    xls = pd.ExcelFile(file_or_path)
    sheets = {}
    if sheet_name:
        sheets[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)
    else:
        for name in xls.sheet_names:
            sheets[name] = pd.read_excel(xls, sheet_name=name)
    return sheets


def import_json(file_or_path) -> pd.DataFrame:
    """
    Import a JSON file. Handles:
    - Array of objects (most common)
    - Meta dashboard MASTER_ALL_DATA.json format (nested datasets)
    - Single object with array values
    """
    if hasattr(file_or_path, "read"):
        content = file_or_path.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        data = json.loads(content)
    else:
        with open(file_or_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    if isinstance(data, list):
        return pd.DataFrame(data)

    if isinstance(data, dict):
        # Meta dashboard MASTER_ALL_DATA.json format: {meta, manifest, datasets}
        if "datasets" in data and isinstance(data["datasets"], dict):
            frames = {}
            for key, records in data["datasets"].items():
                if isinstance(records, list) and records:
                    frames[key] = pd.DataFrame(records)
            return frames if frames else pd.DataFrame()
        # Flat manifest-like JSON with "files" array (from manifest.json)
        if "files" in data and isinstance(data["files"], list):
            return pd.DataFrame(data["files"])
        # Single object with arrays
        if all(isinstance(v, list) for v in data.values()):
            return pd.DataFrame(data)
        # Records-style
        return pd.DataFrame([data])

    return pd.DataFrame()


def import_google_sheet(url: str) -> pd.DataFrame:
    """
    Import a Google Sheet from a public sharing link.
    Converts the URL to CSV export format automatically.
    Supports:
    - https://docs.google.com/spreadsheets/d/ID/edit...
    - https://docs.google.com/spreadsheets/d/ID/gviz/tq?tqx=out:csv
    - Direct CSV export URLs
    """
    parsed = urlparse(url)
    sheet_id = None

    # Extract sheet ID from various URL formats
    if "docs.google.com" in parsed.netloc:
        path_parts = parsed.path.split("/")
        for i, part in enumerate(path_parts):
            if part == "d" and i + 1 < len(path_parts):
                sheet_id = path_parts[i + 1]
                break

    if sheet_id:
        # Try to get specific sheet (gid) from URL
        gid = "0"
        fragment = parsed.fragment
        if "gid=" in fragment:
            gid = fragment.split("gid=")[1].split("&")[0]
        qs = parse_qs(parsed.query)
        if "gid" in qs:
            gid = qs["gid"][0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    else:
        csv_url = url

    resp = requests.get(csv_url, timeout=30)
    resp.raise_for_status()
    return pd.read_csv(io.StringIO(resp.text))


# ---------------------------------------------------------------------------
# META DASHBOARD COMPATIBILITY
# ---------------------------------------------------------------------------

def import_meta_dashboard_output(folder_path: str) -> Dict[str, pd.DataFrame]:
    """
    Import the output of the Meta Ads Dashboard extractor.
    Reads the manifest.json and loads all referenced CSV/JSON files.
    Also handles MASTER_ALL_DATA.xlsx and MASTER_ALL_DATA.json.
    """
    folder = Path(folder_path)
    datasets = {}

    # Try manifest.json first
    manifest_path = folder / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        for file_info in manifest.get("files", []):
            name = file_info.get("name", "")
            csv_path = file_info.get("csv")
            if csv_path:
                # Handle both absolute and relative paths
                abs_csv = Path(csv_path)
                rel_csv = folder / csv_path
                resolved_csv = abs_csv if abs_csv.is_absolute() and abs_csv.exists() else rel_csv
            else:
                resolved_csv = None
            if resolved_csv and resolved_csv.exists():
                datasets[name] = pd.read_csv(resolved_csv, encoding="utf-8-sig")
            else:
                json_path = file_info.get("json")
                if json_path:
                    abs_json = Path(json_path)
                    rel_json = folder / json_path
                    resolved_json = abs_json if abs_json.is_absolute() and abs_json.exists() else rel_json
                else:
                    resolved_json = None
                if resolved_json and resolved_json.exists():
                    with open(resolved_json, "r", encoding="utf-8") as f:
                        datasets[name] = pd.DataFrame(json.load(f))

    # Fallback: try MASTER files
    if not datasets:
        master_xlsx = folder / "MASTER_ALL_DATA.xlsx"
        if master_xlsx.exists():
            datasets = import_excel(str(master_xlsx))
        master_json = folder / "MASTER_ALL_DATA.json"
        if master_json.exists():
            result = import_json(str(master_json))
            if isinstance(result, dict):
                datasets.update(result)
            elif isinstance(result, pd.DataFrame) and not result.empty:
                datasets["master"] = result

    # Fallback: scan for individual CSV files
    if not datasets:
        for csv_file in sorted(folder.rglob("*.csv")):
            name = csv_file.stem
            datasets[name] = pd.read_csv(csv_file, encoding="utf-8-sig")

    return datasets


# ---------------------------------------------------------------------------
# UNIVERSAL AUTO-IMPORT
# ---------------------------------------------------------------------------

def auto_import(source: Any) -> Tuple[str, Any]:
    """
    Auto-detect source type and import.
    Returns (source_type, data) where data is either:
    - pd.DataFrame for single-sheet sources
    - Dict[str, pd.DataFrame] for multi-sheet sources
    """
    if isinstance(source, str):
        # URL
        if source.startswith("http"):
            if "docs.google.com/spreadsheets" in source:
                return "google_sheet", import_google_sheet(source)
            # Generic URL -- try CSV
            resp = requests.get(source, timeout=30)
            resp.raise_for_status()
            return "url_csv", pd.read_csv(io.StringIO(resp.text))

        # File path
        path = Path(source)
        if path.is_dir():
            return "meta_dashboard", import_meta_dashboard_output(source)
        suffix = path.suffix.lower()
        if suffix == ".csv":
            return "csv", import_csv(source)
        if suffix in (".xlsx", ".xls"):
            return "excel", import_excel(source)
        if suffix == ".json":
            result = import_json(source)
            if isinstance(result, dict):
                return "json_multi", result
            return "json", result

    # File-like object (Streamlit upload)
    if hasattr(source, "name"):
        name = source.name.lower()
        if name.endswith(".csv"):
            return "csv", import_csv(source)
        if name.endswith((".xlsx", ".xls")):
            return "excel", import_excel(source)
        if name.endswith(".json"):
            result = import_json(source)
            if isinstance(result, dict):
                return "json_multi", result
            return "json", result

    raise ValueError(f"Cannot determine file type for: {source}")


# ---------------------------------------------------------------------------
# COLUMN MAPPING / NORMALIZATION
# ---------------------------------------------------------------------------

# Common aliases: maps various names to canonical column names
COLUMN_ALIASES = {
    "amount_spent": "spend",
    "amount spent": "spend",
    "cost": "spend",
    "total_spend": "spend",
    "ad_spend": "spend",
    "link_click": "link_clicks",
    "landing_page_view": "landing_page_views",
    "lpv": "landing_page_views",
    "lp_views": "landing_page_views",
    "add_to_cart": "adds_to_cart",
    "atc": "adds_to_cart",
    "checkout": "initiated_checkouts",
    "purchase": "purchases",
    "purchase_value": "purchase_conversion_value",
    "revenue": "purchase_conversion_value",
    "total_revenue": "purchase_conversion_value",
    "conversion_value": "purchase_conversion_value",
    "3s_plays": "video_3s_plays",
    "3_second_plays": "video_3s_plays",
    "video_plays_3s": "video_3s_plays",
    "thruplay": "video_thruplay",
    "thruplay_views": "video_thruplay",
    "video_thruplay_watched": "video_thruplay",
    "unique_link_clicks": "unique_clicks",
    "inline_link_clicks": "link_clicks",
    "outbound_click": "outbound_clicks",
    "inline_link_click_ctr": "outbound_ctr",
    "messaging_first_reply": "messaging_conversations_started",
    "on_facebook_purchase": "purchases",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to canonical form."""
    result = df.copy()
    rename_map = {}
    # Pre-seed with columns that are already in canonical form
    used_targets = set()
    for col in result.columns:
        canonical = col.lower().strip().replace(" ", "_")
        if canonical == col and canonical not in COLUMN_ALIASES:
            used_targets.add(canonical)
    for col in result.columns:
        normalized = col.lower().strip().replace(" ", "_")
        if normalized in COLUMN_ALIASES:
            target = COLUMN_ALIASES[normalized]
            if target in used_targets:
                log.warning("Skipping alias %s -> %s (duplicate target)", col, target)
                continue
            rename_map[col] = target
            used_targets.add(target)
        elif col != normalized:
            if normalized in used_targets:
                log.warning("Skipping rename %s -> %s (duplicate target)", col, normalized)
                continue
            rename_map[col] = normalized
            used_targets.add(normalized)
    if rename_map:
        result = result.rename(columns=rename_map)
    return result
