"""
KPI Engine — Compute standard and custom metrics on DataFrames.
Supports safe division, custom formula evaluation, and aggregation.
"""
import ast
import math
import logging
import operator
import re
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

SAFE_FUNCS = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "pow": pow,
}

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval_node(node: ast.AST, context: Dict[str, float]) -> float:
    """Recursively evaluate an AST node using only approved operations."""
    if isinstance(node, ast.Expression):
        return _safe_eval_node(node.body, context)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id in context:
            return float(context[node.id])
        raise ValueError(f"Unknown variable: {node.id}")
    if isinstance(node, ast.BinOp):
        op_fn = _OPERATORS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        left = _safe_eval_node(node.left, context)
        right = _safe_eval_node(node.right, context)
        return float(op_fn(left, right))
    if isinstance(node, ast.UnaryOp):
        op_fn = _OPERATORS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return float(op_fn(_safe_eval_node(node.operand, context)))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in SAFE_FUNCS:
            raise ValueError(f"Unsupported function call: {ast.dump(node.func)}")
        fn = SAFE_FUNCS[node.func.id]
        args = [_safe_eval_node(a, context) for a in node.args]
        # round() requires int for ndigits; pow() requires int for negative exponents
        if node.func.id == "round" and len(args) > 1:
            args[1] = int(args[1])
        return float(fn(*args))
    raise ValueError(f"Unsupported expression: {type(node).__name__}")


def evaluate_formula(formula: str, context: Dict[str, float], raise_errors: bool = False) -> float:
    """
    Safely evaluate an arithmetic formula string using AST parsing.
    Only allows numeric literals, named variables from context, basic arithmetic,
    and approved math functions (abs, min, max, round, sqrt, log, log10, pow).
    When raise_errors=True, exceptions propagate to the caller for user-facing error messages.
    """
    try:
        tree = ast.parse(formula, mode="eval")
        return _safe_eval_node(tree, context)
    except Exception:
        if raise_errors:
            raise
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


def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Convenience function — compute all standard KPIs on a DataFrame."""
    engine = KPIEngine()
    return engine.compute_all(df)
