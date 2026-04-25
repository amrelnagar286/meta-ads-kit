"""
Meta Ads Ultimate Extractor v4 — Complete extraction engine.
Supports all metrics, all levels, all breakdowns with parallel execution,
pagination, retry logic, action array flattening, and multi-format output.
"""
import os
import re
import io
import json
import time
import threading
import zipfile
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable, Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .meta_catalog import (
    API_VERSION, BASE_URL, PAGE_LIMIT, MAX_WORKERS, MAX_RETRIES,
    DEFAULT_OUTPUT_DIR, DATE_PRESETS, ALL_METRICS, BREAKDOWN_CONFIGS,
    BREAKDOWN_FIELDS, ARRAY_PREFIXES, LEVEL_CONFIGS, DAX_SUGGESTIONS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("MetaAdsExtractor")


class RequestTooLargeError(Exception):
    """Raised when Meta API says the request data is too large."""
    pass


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]+", "_", value.strip()).strip("_").lower()


def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session


class MetaAdsExtractor:
    """Complete Meta Ads insights extraction engine."""

    def __init__(
        self,
        access_token: str,
        ad_account_id: str,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        progress_cb: Optional[Callable] = None,
    ):
        self.access_token = access_token.strip()
        aid = ad_account_id.strip()
        self.ad_account_id = aid if aid.startswith("act_") else f"act_{aid}"
        self.output_dir = output_dir
        self.progress_cb = progress_cb
        self._thread_local = threading.local()
        self.run_started_at = datetime.now()
        self.results: Dict[str, pd.DataFrame] = {}
        self.manifest: Dict[str, Any] = {
            "generated_at": self.run_started_at.isoformat(),
            "account_id": self.ad_account_id,
            "api_version": API_VERSION,
            "files": [],
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # API COMMUNICATION
    # ═══════════════════════════════════════════════════════════════════════════

    def _get_session(self) -> requests.Session:
        """Return a per-thread requests.Session for thread-safe HTTP calls."""
        if not hasattr(self._thread_local, "session"):
            self._thread_local.session = build_session()
        return self._thread_local.session

    def _api_call(
        self,
        endpoint: str,
        params: dict,
        method: str = "GET",
        retry: int = 0,
    ) -> dict:
        url = f"{BASE_URL}/{endpoint}"
        session = self._get_session()
        response = session.request(
            method, url,
            params=params if method == "GET" else None,
            data=params if method != "GET" else None,
            timeout=120,
        )
        try:
            usage = json.loads(
                response.headers.get("x-ad-account-usage", "{}") or "{}"
            )
            if usage.get("acc_id_util_pct", 0) > 75:
                time.sleep(2)
        except Exception:
            pass

        payload = response.json()
        if "error" in payload:
            err = payload["error"]
            code = err.get("code", 0)
            msg = err.get("message", "Unknown API error")
            if code in (17, 32, 613, 80000, 80003) and retry < MAX_RETRIES:
                wait = min((2 ** retry) * 3, 180)
                log.warning(f"Rate limited (code {code}), waiting {wait}s...")
                time.sleep(wait)
                return self._api_call(endpoint, params, method=method, retry=retry + 1)
            if code in (190, 102, 104):
                raise ValueError(f"Token invalid: {msg}")
            if code == 200:
                raise PermissionError(f"Insufficient permissions: {msg}")
            if code == 1 and ("reduce" in msg.lower() or "too large" in msg.lower() or "too much data" in msg.lower()):
                raise RequestTooLargeError(msg)
            if code == 100 and retry < MAX_RETRIES and ("timeout" in msg.lower() or "try again" in msg.lower()):
                wait = min((2 ** retry) * 5, 300)
                log.warning(f"Timeout/transient error (code {code}), waiting {wait}s...")
                time.sleep(wait)
                return self._api_call(endpoint, params, method=method, retry=retry + 1)
            raise RuntimeError(f"Meta API error {code}: {msg}")
        return payload

    def _fetch_all_pages(self, endpoint: str, params: dict) -> List[dict]:
        rows, query = [], params.copy()
        while True:
            payload = self._api_call(endpoint, query)
            rows.extend(payload.get("data", []))
            after = payload.get("paging", {}).get("cursors", {}).get("after")
            if after and payload.get("paging", {}).get("next"):
                query["after"] = after
            else:
                break
        return rows

    # ═══════════════════════════════════════════════════════════════════════════
    # ENTITY FETCHING
    # ═══════════════════════════════════════════════════════════════════════════

    def validate_token(self) -> dict:
        return self._api_call(
            "me",
            {"access_token": self.access_token, "fields": "id,name"},
        )

    def get_account_info(self) -> dict:
        return self._api_call(
            self.ad_account_id,
            {
                "access_token": self.access_token,
                "fields": "id,name,account_status,currency,timezone_name,"
                          "amount_spent,business_country_code",
            },
        )

    def get_campaigns(self) -> List[dict]:
        return self._fetch_all_pages(
            f"{self.ad_account_id}/campaigns",
            {
                "access_token": self.access_token,
                "fields": "id,name,status,objective,buying_type,start_time,"
                          "stop_time,created_time,updated_time,"
                          "daily_budget,lifetime_budget",
                "limit": 500,
            },
        )

    def get_adsets(self) -> List[dict]:
        return self._fetch_all_pages(
            f"{self.ad_account_id}/adsets",
            {
                "access_token": self.access_token,
                "fields": "id,name,status,campaign_id,daily_budget,"
                          "lifetime_budget,bid_strategy,optimization_goal,"
                          "start_time,end_time,targeting",
                "limit": 500,
            },
        )

    def get_ads(self) -> List[dict]:
        return self._fetch_all_pages(
            f"{self.ad_account_id}/ads",
            {
                "access_token": self.access_token,
                "fields": "id,name,status,adset_id,campaign_id,"
                          "created_time,updated_time,"
                          "creative{id,name,thumbnail_url,"
                          "effective_object_story_id}",
                "limit": 500,
            },
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # DATA FLATTENING
    # ═══════════════════════════════════════════════════════════════════════════

    def _flatten_arrays(self, row: dict) -> dict:
        out = {}
        for field, prefix in ARRAY_PREFIXES.items():
            val = row.get(field)
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        key = (
                            item.get("action_type")
                            or item.get("label")
                            or item.get("value_type")
                            or "value"
                        )
                        key = slugify(str(key).replace(".", "_"))
                        value = item.get("value")
                        if value is None:
                            for alt in ("1d_click", "1d_view", "7d_click", "7d_view", "28d_click"):
                                if alt in item:
                                    value = item.get(alt)
                                    break
                        out[f"{prefix}__{key}"] = value
            elif val is not None:
                out[field] = val
        return out

    def flatten_row(self, row: dict) -> dict:
        simple = {}
        for k, v in row.items():
            if (
                k in ALL_METRICS
                or k in BREAKDOWN_FIELDS
                or k in [
                    "date_start", "date_stop",
                    "account_id", "account_name",
                    "campaign_id", "campaign_name",
                    "adset_id", "adset_name",
                    "ad_id", "ad_name",
                ]
            ):
                if not isinstance(v, list):
                    simple[k] = v
        simple.update(self._flatten_arrays(row))
        return simple

    # ═══════════════════════════════════════════════════════════════════════════
    # INSIGHTS FETCHING
    # ═══════════════════════════════════════════════════════════════════════════

    def resolve_date_params(
        self,
        preset: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> dict:
        if start_date and end_date:
            return {"time_range": json.dumps({"since": start_date, "until": end_date})}
        normalized = DATE_PRESETS.get(preset or "last_30d", preset or "last_30d")
        return {"date_preset": normalized}

    def _preset_to_date_range(self, preset: str) -> tuple:
        """Convert a preset string to explicit (start_date, end_date) strings."""
        today = datetime.now().date()
        last_month_end = today.replace(day=1) - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        mapping = {
            "today": (today, today),
            "yesterday": (today - timedelta(days=1), today - timedelta(days=1)),
            "last_3d": (today - timedelta(days=3), today - timedelta(days=1)),
            "last_7d": (today - timedelta(days=7), today - timedelta(days=1)),
            "last_14d": (today - timedelta(days=14), today - timedelta(days=1)),
            "last_28d": (today - timedelta(days=28), today - timedelta(days=1)),
            "last_30d": (today - timedelta(days=30), today - timedelta(days=1)),
            "last_60d": (today - timedelta(days=60), today - timedelta(days=1)),
            "last_90d": (today - timedelta(days=90), today - timedelta(days=1)),
            "this_month": (today.replace(day=1), today),
            "last_month": (last_month_start, last_month_end),
            "this_quarter": (today.replace(month=quarter_month, day=1), today),
            "this_year": (today.replace(month=1, day=1), today),
            "last_year": (today.replace(year=today.year - 1, month=1, day=1),
                          today.replace(year=today.year - 1, month=12, day=31)),
            "maximum": (today.replace(year=today.year - 5, month=1, day=1), today),
        }
        if preset in mapping:
            s, e = mapping[preset]
            return s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d")
        return (today - timedelta(days=30)).strftime("%Y-%m-%d"), (today - timedelta(days=1)).strftime("%Y-%m-%d")

    def _split_date_range(self, start: str, end: str, chunk_days: int = 7) -> List[tuple]:
        """Split a date range into smaller chunks for large requests."""
        start_dt = datetime.strptime(start, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end, "%Y-%m-%d").date()
        chunks = []
        cursor = start_dt
        while cursor <= end_dt:
            chunk_end = min(cursor + timedelta(days=chunk_days - 1), end_dt)
            chunks.append((cursor.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")))
            cursor = chunk_end + timedelta(days=1)
        return chunks

    def _build_insights_params(
        self,
        level: str,
        breakdown_key: str,
        time_increment: Any,
        selected_metrics: Optional[List[str]],
        attribution_windows: Optional[List[str]],
        filtering: Optional[List[dict]],
        action_report_time: str,
        campaign_ids: Optional[List[str]],
    ) -> dict:
        """Build the base params dict for an insights query (without date params)."""
        breakdown_cfg = BREAKDOWN_CONFIGS[breakdown_key]
        metrics = selected_metrics or breakdown_cfg["metrics"]
        params = {
            "access_token": self.access_token,
            "level": level,
            "fields": ",".join(metrics),
            "limit": PAGE_LIMIT,
            "time_increment": time_increment,
            "action_report_time": action_report_time,
        }
        if breakdown_cfg["breakdowns"]:
            params["breakdowns"] = ",".join(breakdown_cfg["breakdowns"])
        if attribution_windows:
            params["action_attribution_windows"] = json.dumps(attribution_windows)

        filter_list = list(filtering) if filtering else []
        if campaign_ids:
            filter_list.append({
                "field": "campaign.id",
                "operator": "IN",
                "value": campaign_ids,
            })
        if filter_list:
            params["filtering"] = json.dumps(filter_list)
        return params

    def _fetch_insights_chunked(
        self,
        params: dict,
        start_date: str,
        end_date: str,
        chunk_days: int = 7,
    ) -> List[dict]:
        """Fetch insights in date chunks when a single request is too large."""
        chunks = self._split_date_range(start_date, end_date, chunk_days)
        all_rows = []
        log.info(f"Splitting {start_date}..{end_date} into {len(chunks)} chunks of {chunk_days} days")
        for i, (cs, ce) in enumerate(chunks):
            chunk_params = params.copy()
            chunk_params["time_range"] = json.dumps({"since": cs, "until": ce})
            chunk_params.pop("date_preset", None)
            try:
                rows = self._fetch_all_pages(f"{self.ad_account_id}/insights", chunk_params)
                all_rows.extend(rows)
                log.info(f"Chunk {i+1}/{len(chunks)} ({cs} to {ce}): {len(rows)} rows")
            except RequestTooLargeError:
                if chunk_days > 1:
                    log.warning(f"Chunk still too large, splitting further with {max(1, chunk_days // 2)} day chunks")
                    sub_rows = self._fetch_insights_chunked(params, cs, ce, max(1, chunk_days // 2))
                    all_rows.extend(sub_rows)
                else:
                    log.error(f"Cannot split further — single day {cs} still too large, skipping")
            except Exception as e:
                log.warning(f"Chunk {cs}..{ce} failed: {e}, continuing with remaining chunks")
        return all_rows

    def _fetch_async_report(self, params: dict) -> List[dict]:
        """Use Meta's async report endpoint for very large queries."""
        post_params = params.copy()
        try:
            report = self._api_call(
                f"{self.ad_account_id}/insights",
                post_params,
                method="POST",
            )
            report_id = report.get("report_run_id")
            if not report_id:
                raise RuntimeError("No report_run_id in async response")

            log.info(f"Async report started: {report_id}")
            for attempt in range(120):
                time.sleep(5)
                status = self._api_call(report_id, {"access_token": self.access_token})
                pct = status.get("async_percent_completion", 0)
                if status.get("async_status") == "Job Completed":
                    log.info(f"Async report {report_id} complete")
                    return self._fetch_all_pages(
                        f"{report_id}/insights",
                        {"access_token": self.access_token, "limit": PAGE_LIMIT},
                    )
                if status.get("async_status") == "Job Failed":
                    raise RuntimeError(f"Async report failed: {status}")
                if attempt % 12 == 0:
                    log.info(f"Async report {pct}% complete...")
            raise RuntimeError("Async report timed out after 10 minutes")
        except Exception as e:
            log.error(f"Async report failed: {e}")
            raise

    def fetch_insights(
        self,
        level: str,
        breakdown_key: str,
        preset: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        time_increment: Any = 1,
        selected_metrics: Optional[List[str]] = None,
        attribution_windows: Optional[List[str]] = None,
        filtering: Optional[List[dict]] = None,
        action_report_time: str = "mixed",
        campaign_ids: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        params = self._build_insights_params(
            level, breakdown_key, time_increment, selected_metrics,
            attribution_windows, filtering, action_report_time, campaign_ids,
        )
        params.update(self.resolve_date_params(preset, start_date, end_date))

        # Resolve date range for fallback chunking
        if start_date and end_date:
            resolved_start, resolved_end = start_date, end_date
        elif preset:
            resolved_start, resolved_end = self._preset_to_date_range(
                DATE_PRESETS.get(preset, preset)
            )
        else:
            resolved_start, resolved_end = self._preset_to_date_range("last_30d")

        breakdown_cfg = BREAKDOWN_CONFIGS[breakdown_key]
        rows = []
        try:
            rows = self._fetch_all_pages(f"{self.ad_account_id}/insights", params)
        except RequestTooLargeError:
            log.warning(f"Request too large for {level} x {breakdown_key}, trying chunked fetch...")
            try:
                rows = self._fetch_insights_chunked(params, resolved_start, resolved_end, chunk_days=7)
            except Exception:
                log.warning(f"Chunked fetch failed, trying async report...")
                try:
                    async_params = params.copy()
                    async_params["time_range"] = json.dumps({"since": resolved_start, "until": resolved_end})
                    async_params.pop("date_preset", None)
                    rows = self._fetch_async_report(async_params)
                except Exception as e:
                    log.error(f"All strategies failed for {level} x {breakdown_key}: {e}")
                    return pd.DataFrame()
        except Exception as e:
            log.error(f"Failed {level} x {breakdown_key}: {e}")
            return pd.DataFrame()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame([self.flatten_row(r) for r in rows])
        df["_level"] = level
        df["_breakdown_key"] = breakdown_key
        df["_breakdown_label"] = breakdown_cfg["label"]
        df["_extracted_at"] = datetime.now().isoformat()
        return df

    # ═══════════════════════════════════════════════════════════════════════════
    # OUTPUT GENERATION
    # ═══════════════════════════════════════════════════════════════════════════

    def save_dataframe_bundle(
        self, df: pd.DataFrame, base_name: str, folder: str
    ) -> Dict[str, str]:
        os.makedirs(folder, exist_ok=True)
        csv_path = os.path.join(folder, f"{base_name}.csv")
        json_path = os.path.join(folder, f"{base_name}.json")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(
                df.to_dict(orient="records"), f,
                ensure_ascii=False, indent=2, default=str,
            )
        self.manifest["files"].append({
            "name": base_name,
            "csv": csv_path,
            "json": json_path,
            "rows": int(len(df)),
        })
        return {"csv": csv_path, "json": json_path}

    def _build_master_files(self, base_dir: str) -> None:
        excel_path = os.path.join(base_dir, "MASTER_ALL_DATA.xlsx")
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            manifest_df = pd.DataFrame(self.manifest["files"])
            if not manifest_df.empty:
                manifest_df.to_excel(writer, index=False, sheet_name="manifest")
            for name, df in self.results.items():
                if df is not None and not df.empty:
                    sheet = slugify(name)[:31] or "sheet"
                    df.to_excel(writer, index=False, sheet_name=sheet)

        master_json_path = os.path.join(base_dir, "MASTER_ALL_DATA.json")
        payload = {
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "account_id": self.ad_account_id,
                "api_version": API_VERSION,
            },
            "manifest": self.manifest,
            "datasets": {
                k: v.to_dict(orient="records")
                for k, v in self.results.items()
                if v is not None and not v.empty
            },
        }
        with open(master_json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

        self.manifest["master_excel"] = excel_path
        self.manifest["master_json"] = master_json_path

        # Power BI pack
        pbi_dir = os.path.join(base_dir, "powerbi")
        os.makedirs(pbi_dir, exist_ok=True)

        pq_template = (
            "let\n"
            '    Source = Folder.Files("{{FOLDER_PATH}}"),\n'
            '    Filtered = Table.SelectRows(Source, each Text.EndsWith([Extension], ".csv")),\n'
            '    Visible = Table.SelectRows(Filtered, each [Attributes]?[Hidden]? <> true),\n'
            '    WithTables = Table.AddColumn(Visible, "Data", each Csv.Document([Content],[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv])),\n'
            '    Promoted = Table.AddColumn(WithTables, "Promoted", each Table.PromoteHeaders([Data], [PromoteAllScalars=true]))\n'
            "in\n"
            "    Promoted"
        )
        with open(os.path.join(pbi_dir, "power_query_folder_import.m"), "w", encoding="utf-8") as f:
            f.write(pq_template)
        with open(os.path.join(pbi_dir, "dax_suggestions.json"), "w", encoding="utf-8") as f:
            json.dump(DAX_SUGGESTIONS, f, ensure_ascii=False, indent=2)

        manifest_path = os.path.join(base_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2, default=str)

    # ═══════════════════════════════════════════════════════════════════════════
    # MAIN EXTRACTION RUN
    # ═══════════════════════════════════════════════════════════════════════════

    def run(
        self,
        levels: List[str],
        breakdowns: List[str],
        campaign_ids: Optional[List[str]] = None,
        preset: Optional[str] = "last_30d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        time_increment: Any = 1,
        selected_metrics: Optional[List[str]] = None,
        attribution_windows: Optional[List[str]] = None,
        filtering: Optional[List[dict]] = None,
        action_report_time: str = "mixed",
        include_entities: bool = True,
    ) -> Dict[str, Any]:
        run_slug = self.run_started_at.strftime("run_%Y%m%d_%H%M%S")
        base_dir = os.path.join(self.output_dir, run_slug)
        raw_dir = os.path.join(base_dir, "raw")
        os.makedirs(raw_dir, exist_ok=True)

        if include_entities:
            entities_dir = os.path.join(base_dir, "entities")
            try:
                acc = pd.DataFrame([self.get_account_info()])
                self.save_dataframe_bundle(acc, "account_info", entities_dir)
            except Exception as e:
                log.warning(f"Could not fetch account info: {e}")

            try:
                campaigns = pd.DataFrame(self.get_campaigns())
                if not campaigns.empty:
                    self.save_dataframe_bundle(campaigns, "campaigns", entities_dir)
            except Exception as e:
                log.warning(f"Could not fetch campaigns: {e}")

            try:
                adsets = pd.DataFrame(self.get_adsets())
                if not adsets.empty:
                    self.save_dataframe_bundle(adsets, "adsets", entities_dir)
            except Exception as e:
                log.warning(f"Could not fetch adsets: {e}")

            try:
                ads = pd.DataFrame(self.get_ads())
                if not ads.empty:
                    self.save_dataframe_bundle(ads, "ads", entities_dir)
            except Exception as e:
                log.warning(f"Could not fetch ads: {e}")

        tasks = [(level, bd) for level in levels for bd in breakdowns]
        total = len(tasks)
        done = 0

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futs = {
                pool.submit(
                    self.fetch_insights, level, bd, preset, start_date,
                    end_date, time_increment, selected_metrics,
                    attribution_windows, filtering, action_report_time,
                    campaign_ids,
                ): (level, bd)
                for level, bd in tasks
            }
            for fut in as_completed(futs):
                level, bd = futs[fut]
                done += 1
                try:
                    df = fut.result()
                except Exception as e:
                    log.error(f"Task {level} x {bd} failed: {e}")
                    df = pd.DataFrame()
                if self.progress_cb:
                    self.progress_cb(f"{done}/{total} {level} x {bd}", done, total)
                base_name = f"{level}__{bd}"
                self.results[base_name] = df
                if not df.empty:
                    self.save_dataframe_bundle(df, base_name, raw_dir)

        self._build_master_files(base_dir)
        return {
            "output_dir": base_dir,
            "manifest": self.manifest,
            "summary": self.summary(),
        }

    def zip_output(self, output_dir: str) -> str:
        zip_path = f"{output_dir}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(output_dir):
                for file in files:
                    full = os.path.join(root, file)
                    zf.write(full, os.path.relpath(full, output_dir))
        return zip_path

    def summary(self) -> Dict[str, Any]:
        return {
            k: int(len(v)) if isinstance(v, pd.DataFrame) else 0
            for k, v in self.results.items()
        }
