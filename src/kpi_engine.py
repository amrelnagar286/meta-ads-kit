"""
KPI Engine — Compute standard and custom metrics on DataFrames.
Supports safe division, custom formula evaluation, and aggregation.
"""
import re
import math
import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from .helpers import safe_divide

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# STANDARD KPIs
# ═══════════════════════════════════════════════════════════════════════════════

STANDARD_KPIS = {
    "roas": {
        "name": "ROAS",
        "formula": "revenue / spend",
        "required": ["revenue", "spend"],
        "unit": "ratio",
        "format": ".2f",
    },
    "cpa": {
        "name": "CPA",
        "formula": "spend / conversions",
        "required": ["spend", "conversions"],
        "unit": "currency",
        "format": ".2f",
    },
    "ctr": {
        "name": "CTR",
        "formula": "clicks / impressions * 100",
        "required": ["clicks", "impressions"],
        "unit": "percentage",
        "format": ".2f",
    },
    "cpc": {
        "name": "CPC",
        "formula": "spend / clicks",
        "required": ["spend", "clicks"],
        "unit": "currency",
        "format": ".2f",
    },
    "cpm": {
        "name": "CPM",
        "formula": "(spend / impressions) * 1000",
        "required": ["spend", "impressions"],
        "unit": "currency",
        "format": ".2f",
    },
    "cvr": {
        "name": "CVR",
        "formula": "conversions / clicks * 100",
        "required": ["conversions", "clicks"],
        "unit": "percentage",
        "format": ".2f",
    },
    "aov": {
        "name": "AOV",
        "formula": "revenue / purchases",
        "required": ["revenue", "purchases"],
        "unit": "currency",
        "format": ".2f",
    },
    "frequency": {
        "name": "Frequency",
        "formula": "impressions / reach",
        "required": ["impressions", "reach"],
        "unit": "ratio",
        "format": ".2f",
    },
    "cpl": {
        "name": "Cost Per Lead",
        "formula": "spend / leads",
        "required": ["spend", "leads"],
        "unit": "currency",
        "format": ".2f",
    },
    "thruplay_rate": {
        "name": "ThruPlay Rate",
        "formula": "thruplay / impressions * 100",
        "required": ["thruplay", "impressions"],
        "unit": "percentage",
        "format": ".2f",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# FORMULA PARSER — SAFE EVALUATION WITH COLUMN REFERENCES
# ═══════════════════════════════════════════════════════════════════════════════

SAFE_MATH = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "pow": pow,
}


def evaluate_formula(formula: str, context: Dict[str, float]) -> float:
    """
    Safely evaluate a formula string using only the supplied variable context.
    No access to builtins or dangerous functions.
    """
    try:
        allowed = dict(SAFE_MATH)
        allowed.update(context)
        allowed["__builtins__"] = {}
        result = eval(formula, allowed)
        if isinstance(result, (int, float)):
            return float(result)
        return 0.0
    except Exception:
        return 0.0


class KPIEngine:
    """Compute KPIs on DataFrames with standard and custom formulas."""

    def __init__(self, custom_kpis: Optional[List[Dict]] = None):
        self.custom_kpis = custom_kpis or []

    def compute_standard_kpi(
        self, kpi_id: str, row: Dict[str, Any]
    ) -> float:
        kpi = STANDARD_KPIS.get(kpi_id)
        if not kpi:
            return 0.0
        context = {}
        for field in kpi["required"]:
            try:
                context[field] = float(row.get(field, 0) or 0)
            except (ValueError, TypeError):
                context[field] = 0.0
        return evaluate_formula(kpi["formula"], context)

    def compute_kpi_on_dataframe(
        self, df: pd.DataFrame, kpi_id: str
    ) -> pd.Series:
        kpi = STANDARD_KPIS.get(kpi_id)
        if not kpi:
            return pd.Series(0.0, index=df.index)

        required = kpi["required"]
        available = [f for f in required if f in df.columns]
        if len(available) < len(required):
            return pd.Series(0.0, index=df.index)

        if len(required) == 2:
            a = pd.to_numeric(df[required[0]], errors="coerce").fillna(0)
            b = pd.to_numeric(df[required[1]], errors="coerce").fillna(0)
            formula = kpi["formula"]
            if "* 1000" in formula:
                return (a / b.replace(0, float("nan"))).fillna(0) * 1000
            if "* 100" in formula:
                return (a / b.replace(0, float("nan"))).fillna(0) * 100
            return (a / b.replace(0, float("nan"))).fillna(0)
        return pd.Series(0.0, index=df.index)

    def compute_custom_kpi(
        self, kpi_def: Dict, row: Dict[str, Any]
    ) -> float:
        formula = kpi_def.get("formula", "0")
        context = {}
        for field in kpi_def.get("required_fields", []):
            try:
                context[field] = float(row.get(field, 0) or 0)
            except (ValueError, TypeError):
                context[field] = 0.0
        return evaluate_formula(formula, context)

    def compute_all(
        self, df: pd.DataFrame, kpi_ids: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Add KPI columns to the DataFrame."""
        ids_to_compute = kpi_ids or list(STANDARD_KPIS.keys())
        result = df.copy()
        for kpi_id in ids_to_compute:
            col_name = f"kpi_{kpi_id}"
            result[col_name] = self.compute_kpi_on_dataframe(result, kpi_id)
        for custom in self.custom_kpis:
            cid = custom.get("kpi_id", "custom")
            col_name = f"kpi_{cid}"
            result[col_name] = result.apply(
                lambda row, kd=custom: self.compute_custom_kpi(kd, row.to_dict()),
                axis=1,
            )
        return result

    def aggregate_kpis(
        self, df: pd.DataFrame, group_by: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Aggregate numeric columns with proper KPI recalculation."""
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not group_by:
            totals = {}
            for col in numeric_cols:
                totals[col] = df[col].sum()
            result = pd.DataFrame([totals])
            return self.compute_all(result)

        group_cols = [c for c in group_by if c in df.columns]
        if not group_cols:
            return df
        agg = df.groupby(group_cols)[numeric_cols].sum().reset_index()
        return self.compute_all(agg)
