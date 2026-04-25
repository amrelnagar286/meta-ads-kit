"""
Meta API Manager — Full write operations for campaign, ad set, ad, audience, and creative management.
Complete replacement for Meta Ads Manager: create, update, delete, duplicate, status control.
"""
import json
import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

import requests

from .meta_catalog import API_VERSION, BASE_URL, MAX_RETRIES

log = logging.getLogger(__name__)


class MetaAPIManager:
    """Full Meta Ads API management — read and write operations."""

    def __init__(self, access_token: str, ad_account_id: str):
        self.access_token = access_token.strip()
        aid = ad_account_id.strip()
        self.ad_account_id = aid if aid.startswith("act_") else f"act_{aid}"
        self.session = requests.Session()

    def _call(self, endpoint: str, params: dict, method: str = "GET", retry: int = 0) -> dict:
        url = f"{BASE_URL}/{endpoint}"
        kw = {"params": params} if method == "GET" else {"data": params}
        resp = self.session.request(method, url, timeout=120, **kw)
        payload = resp.json()
        if "error" in payload:
            err = payload["error"]
            code = err.get("code", 0)
            msg = err.get("message", "Unknown")
            if code in (17, 32, 613, 80000, 80003) and retry < MAX_RETRIES:
                wait = min((2 ** retry) * 3, 180)
                time.sleep(wait)
                return self._call(endpoint, params, method, retry + 1)
            raise RuntimeError(f"Meta API error {code}: {msg}")
        return payload

    def _paginate(self, endpoint: str, params: dict) -> List[dict]:
        rows, q = [], params.copy()
        while True:
            payload = self._call(endpoint, q)
            rows.extend(payload.get("data", []))
            after = payload.get("paging", {}).get("cursors", {}).get("after")
            if after and payload.get("paging", {}).get("next"):
                q["after"] = after
            else:
                break
        return rows

    # ═══════════════════════════════════════════════════════════════════════════
    # ACCOUNT
    # ═══════════════════════════════════════════════════════════════════════════

    def get_account_info(self) -> dict:
        return self._call(self.ad_account_id, {
            "access_token": self.access_token,
            "fields": "id,name,account_status,currency,timezone_name,"
                      "amount_spent,balance,business_country_code,"
                      "spend_cap,funding_source_details,owner,"
                      "min_campaign_group_spend_cap,business",
        })

    def get_account_users(self) -> List[dict]:
        return self._paginate(f"{self.ad_account_id}/users", {
            "access_token": self.access_token,
            "fields": "id,name,role,email",
        })

    # ═══════════════════════════════════════════════════════════════════════════
    # CAMPAIGNS — FULL CRUD
    # ═══════════════════════════════════════════════════════════════════════════

    def get_campaigns(self, status_filter: Optional[List[str]] = None) -> List[dict]:
        params = {
            "access_token": self.access_token,
            "fields": "id,name,status,effective_status,objective,buying_type,"
                      "start_time,stop_time,created_time,updated_time,"
                      "daily_budget,lifetime_budget,budget_remaining,"
                      "spend_cap,bid_strategy,special_ad_categories",
            "limit": 500,
        }
        if status_filter:
            params["filtering"] = json.dumps([{
                "field": "effective_status",
                "operator": "IN",
                "value": status_filter,
            }])
        return self._paginate(f"{self.ad_account_id}/campaigns", params)

    def create_campaign(self, name: str, objective: str, status: str = "PAUSED",
                        daily_budget: Optional[float] = None,
                        lifetime_budget: Optional[float] = None,
                        bid_strategy: Optional[str] = None,
                        special_ad_categories: Optional[List[str]] = None) -> dict:
        params = {
            "access_token": self.access_token,
            "name": name,
            "objective": objective,
            "status": status,
        }
        if daily_budget:
            params["daily_budget"] = int(round(float(daily_budget) * 100))
        if lifetime_budget:
            params["lifetime_budget"] = int(round(float(lifetime_budget) * 100))
        if bid_strategy:
            params["bid_strategy"] = bid_strategy
        if special_ad_categories is not None:
            params["special_ad_categories"] = json.dumps(special_ad_categories)
        return self._call(f"{self.ad_account_id}/campaigns", params, method="POST")

    def update_campaign(self, campaign_id: str, **kwargs) -> dict:
        params = {"access_token": self.access_token}
        for k, v in kwargs.items():
            if k in ("daily_budget", "lifetime_budget") and v is not None:
                params[k] = int(round(float(v) * 100))
            elif v is not None:
                params[k] = v
        return self._call(campaign_id, params, method="POST")

    def delete_campaign(self, campaign_id: str) -> dict:
        return self._call(campaign_id, {
            "access_token": self.access_token, "status": "DELETED",
        }, method="POST")

    def duplicate_campaign(self, campaign_id: str, new_name: Optional[str] = None) -> dict:
        params = {
            "access_token": self.access_token,
            "deep_copy": True,
            "status_option": "PAUSED",
        }
        if new_name:
            params["rename_options"] = json.dumps({"rename_suffix": f" - {new_name}"})
        return self._call(f"{campaign_id}/copies", params, method="POST")

    # ═══════════════════════════════════════════════════════════════════════════
    # AD SETS — FULL CRUD
    # ═══════════════════════════════════════════════════════════════════════════

    def get_adsets(self, campaign_id: Optional[str] = None,
                   status_filter: Optional[List[str]] = None) -> List[dict]:
        endpoint = f"{campaign_id}/adsets" if campaign_id else f"{self.ad_account_id}/adsets"
        params = {
            "access_token": self.access_token,
            "fields": "id,name,status,effective_status,campaign_id,"
                      "daily_budget,lifetime_budget,budget_remaining,"
                      "bid_strategy,bid_amount,optimization_goal,"
                      "billing_event,start_time,end_time,"
                      "targeting,promoted_object,attribution_spec,"
                      "destination_type,created_time,updated_time",
            "limit": 500,
        }
        if status_filter:
            params["filtering"] = json.dumps([{
                "field": "effective_status", "operator": "IN", "value": status_filter,
            }])
        return self._paginate(endpoint, params)

    def create_adset(self, campaign_id: str, name: str, daily_budget: float,
                     optimization_goal: str, billing_event: str,
                     targeting: dict, status: str = "PAUSED",
                     bid_strategy: Optional[str] = None,
                     bid_amount: Optional[float] = None,
                     start_time: Optional[str] = None,
                     end_time: Optional[str] = None,
                     promoted_object: Optional[dict] = None) -> dict:
        params = {
            "access_token": self.access_token,
            "campaign_id": campaign_id,
            "name": name,
            "daily_budget": int(round(float(daily_budget) * 100)),
            "optimization_goal": optimization_goal,
            "billing_event": billing_event,
            "targeting": json.dumps(targeting),
            "status": status,
        }
        if bid_strategy:
            params["bid_strategy"] = bid_strategy
        if bid_amount:
            params["bid_amount"] = int(round(float(bid_amount) * 100))
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if promoted_object:
            params["promoted_object"] = json.dumps(promoted_object)
        return self._call(f"{self.ad_account_id}/adsets", params, method="POST")

    def update_adset(self, adset_id: str, **kwargs) -> dict:
        params = {"access_token": self.access_token}
        for k, v in kwargs.items():
            if k in ("daily_budget", "lifetime_budget", "bid_amount") and v is not None:
                params[k] = int(round(float(v) * 100))
            elif k == "targeting" and isinstance(v, dict):
                params[k] = json.dumps(v)
            elif v is not None:
                params[k] = v
        return self._call(adset_id, params, method="POST")

    def delete_adset(self, adset_id: str) -> dict:
        return self._call(adset_id, {
            "access_token": self.access_token, "status": "DELETED",
        }, method="POST")

    def duplicate_adset(self, adset_id: str, campaign_id: Optional[str] = None) -> dict:
        params = {"access_token": self.access_token, "deep_copy": True, "status_option": "PAUSED"}
        if campaign_id:
            params["campaign_id"] = campaign_id
        return self._call(f"{adset_id}/copies", params, method="POST")

    # ═══════════════════════════════════════════════════════════════════════════
    # ADS — FULL CRUD
    # ═══════════════════════════════════════════════════════════════════════════

    def get_ads(self, adset_id: Optional[str] = None,
                status_filter: Optional[List[str]] = None) -> List[dict]:
        endpoint = f"{adset_id}/ads" if adset_id else f"{self.ad_account_id}/ads"
        params = {
            "access_token": self.access_token,
            "fields": "id,name,status,effective_status,adset_id,campaign_id,"
                      "created_time,updated_time,tracking_specs,"
                      "creative{id,name,title,body,image_url,thumbnail_url,"
                      "effective_object_story_id,object_story_spec,"
                      "call_to_action_type,link_url,url_tags}",
            "limit": 500,
        }
        if status_filter:
            params["filtering"] = json.dumps([{
                "field": "effective_status", "operator": "IN", "value": status_filter,
            }])
        return self._paginate(endpoint, params)

    def create_ad(self, adset_id: str, name: str, creative_id: str,
                  status: str = "PAUSED", tracking_specs: Optional[dict] = None) -> dict:
        params = {
            "access_token": self.access_token,
            "adset_id": adset_id,
            "name": name,
            "creative": json.dumps({"creative_id": creative_id}),
            "status": status,
        }
        if tracking_specs:
            params["tracking_specs"] = json.dumps(tracking_specs)
        return self._call(f"{self.ad_account_id}/ads", params, method="POST")

    def update_ad(self, ad_id: str, **kwargs) -> dict:
        params = {"access_token": self.access_token}
        params.update({k: v for k, v in kwargs.items() if v is not None})
        return self._call(ad_id, params, method="POST")

    def delete_ad(self, ad_id: str) -> dict:
        return self._call(ad_id, {
            "access_token": self.access_token, "status": "DELETED",
        }, method="POST")

    # ═══════════════════════════════════════════════════════════════════════════
    # CREATIVES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_creatives(self) -> List[dict]:
        return self._paginate(f"{self.ad_account_id}/adcreatives", {
            "access_token": self.access_token,
            "fields": "id,name,title,body,image_url,thumbnail_url,"
                      "effective_object_story_id,object_story_spec,"
                      "call_to_action_type,link_url,url_tags,"
                      "status,object_type",
            "limit": 500,
        })

    def create_creative(self, name: str, object_story_spec: dict) -> dict:
        return self._call(f"{self.ad_account_id}/adcreatives", {
            "access_token": self.access_token,
            "name": name,
            "object_story_spec": json.dumps(object_story_spec),
        }, method="POST")

    def upload_image(self, image_path: str) -> dict:
        url = f"{BASE_URL}/{self.ad_account_id}/adimages"
        with open(image_path, "rb") as f:
            resp = self.session.post(url, data={
                "access_token": self.access_token,
            }, files={"filename": f}, timeout=120)
        return resp.json()

    def get_ad_images(self) -> List[dict]:
        return self._paginate(f"{self.ad_account_id}/adimages", {
            "access_token": self.access_token,
            "fields": "id,hash,name,url,width,height,created_time,status",
            "limit": 500,
        })

    def upload_video(self, video_path: str, title: str = "") -> dict:
        url = f"{BASE_URL}/{self.ad_account_id}/advideos"
        with open(video_path, "rb") as f:
            resp = self.session.post(url, data={
                "access_token": self.access_token,
                "title": title,
            }, files={"source": f}, timeout=300)
        return resp.json()

    def get_ad_videos(self) -> List[dict]:
        return self._paginate(f"{self.ad_account_id}/advideos", {
            "access_token": self.access_token,
            "fields": "id,title,length,source,picture,created_time,updated_time",
            "limit": 100,
        })

    # ═══════════════════════════════════════════════════════════════════════════
    # AUDIENCES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_custom_audiences(self) -> List[dict]:
        return self._paginate(f"{self.ad_account_id}/customaudiences", {
            "access_token": self.access_token,
            "fields": "id,name,description,subtype,approximate_count,"
                      "data_source,delivery_status,operation_status,"
                      "permission_for_actions,time_created,time_updated,"
                      "lookalike_spec,retention_days",
            "limit": 500,
        })

    def create_custom_audience(self, name: str, description: str = "",
                                subtype: str = "CUSTOM",
                                customer_file_source: Optional[str] = None) -> dict:
        params = {
            "access_token": self.access_token,
            "name": name,
            "description": description,
            "subtype": subtype,
        }
        if customer_file_source:
            params["customer_file_source"] = customer_file_source
        return self._call(f"{self.ad_account_id}/customaudiences", params, method="POST")

    def create_lookalike_audience(self, name: str, origin_audience_id: str,
                                  country: str, ratio: float = 0.01) -> dict:
        return self._call(f"{self.ad_account_id}/customaudiences", {
            "access_token": self.access_token,
            "name": name,
            "subtype": "LOOKALIKE",
            "origin_audience_id": origin_audience_id,
            "lookalike_spec": json.dumps({
                "type": "similarity",
                "country": country,
                "ratio": ratio,
            }),
        }, method="POST")

    def get_saved_audiences(self) -> List[dict]:
        return self._paginate(f"{self.ad_account_id}/saved_audiences", {
            "access_token": self.access_token,
            "fields": "id,name,description,targeting,approximate_count,"
                      "run_status,time_created,time_updated",
            "limit": 500,
        })

    def create_saved_audience(self, name: str, targeting: dict) -> dict:
        return self._call(f"{self.ad_account_id}/saved_audiences", {
            "access_token": self.access_token,
            "name": name,
            "targeting": json.dumps(targeting),
        }, method="POST")

    def get_targeting_search(self, query: str, target_type: str = "adinterest") -> List[dict]:
        return self._call("search", {
            "access_token": self.access_token,
            "type": target_type,
            "q": query,
        }).get("data", [])

    def estimate_reach(self, targeting: dict, optimization_goal: str = "LINK_CLICKS") -> dict:
        return self._call(f"{self.ad_account_id}/reachestimate", {
            "access_token": self.access_token,
            "targeting_spec": json.dumps(targeting),
            "optimization_goal": optimization_goal,
        })

    # ═══════════════════════════════════════════════════════════════════════════
    # PIXELS & CONVERSIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_pixels(self) -> List[dict]:
        return self._paginate(f"{self.ad_account_id}/adspixels", {
            "access_token": self.access_token,
            "fields": "id,name,code,creation_time,last_fired_time,"
                      "is_unavailable,data_use_setting",
        })

    def get_pixel_stats(self, pixel_id: str) -> dict:
        return self._call(f"{pixel_id}/stats", {
            "access_token": self.access_token,
        })

    def get_custom_conversions(self) -> List[dict]:
        return self._paginate(f"{self.ad_account_id}/customconversions", {
            "access_token": self.access_token,
            "fields": "id,name,description,pixel,rule,"
                      "default_conversion_value,event_source_type,"
                      "first_fired_time,last_fired_time,is_archived",
        })

    # ═══════════════════════════════════════════════════════════════════════════
    # BATCH STATUS UPDATES
    # ═══════════════════════════════════════════════════════════════════════════

    def batch_update_status(self, entity_ids: List[str], status: str) -> List[dict]:
        results = []
        for eid in entity_ids:
            try:
                r = self._call(eid, {
                    "access_token": self.access_token, "status": status,
                }, method="POST")
                results.append({"id": eid, "status": "success", "result": r})
            except Exception as e:
                results.append({"id": eid, "status": "error", "error": str(e)})
        return results

    def batch_update_budgets(self, updates: List[Dict[str, Any]]) -> List[dict]:
        results = []
        for upd in updates:
            try:
                eid = upd["id"]
                params = {"access_token": self.access_token}
                if "daily_budget" in upd:
                    params["daily_budget"] = int(round(float(upd["daily_budget"]) * 100))
                if "lifetime_budget" in upd:
                    params["lifetime_budget"] = int(round(float(upd["lifetime_budget"]) * 100))
                r = self._call(eid, params, method="POST")
                results.append({"id": eid, "status": "success", "result": r})
            except Exception as e:
                results.append({"id": upd.get("id", "?"), "status": "error", "error": str(e)})
        return results

    # ═══════════════════════════════════════════════════════════════════════════
    # ACTIVITY LOG
    # ═══════════════════════════════════════════════════════════════════════════

    def get_activities(self, since: Optional[str] = None, limit: int = 100) -> List[dict]:
        params = {
            "access_token": self.access_token,
            "fields": "event_type,event_time,object_id,object_name,"
                      "object_type,actor_id,actor_name,extra_data,"
                      "translated_event_type",
            "limit": limit,
        }
        if since:
            params["since"] = since
        return self._paginate(f"{self.ad_account_id}/activities", params)

    # ═══════════════════════════════════════════════════════════════════════════
    # AD PREVIEWS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_ad_preview(self, ad_id: str, ad_format: str = "DESKTOP_FEED_STANDARD") -> dict:
        return self._call(f"{ad_id}/previews", {
            "access_token": self.access_token,
            "ad_format": ad_format,
        })

    def get_creative_preview(self, creative_id: str,
                              ad_format: str = "DESKTOP_FEED_STANDARD") -> dict:
        return self._call(f"{creative_id}/previews", {
            "access_token": self.access_token,
            "ad_format": ad_format,
        })

    # ═══════════════════════════════════════════════════════════════════════════
    # TARGETING BROWSE
    # ═══════════════════════════════════════════════════════════════════════════

    def get_targeting_browse(self) -> List[dict]:
        return self._paginate(f"{self.ad_account_id}/targetingbrowse", {
            "access_token": self.access_token,
            "limit": 500,
        })
