"""
Multi-Source Data Linker -- Join/merge datasets across sources.
Supports linking Meta ad_id to order sheets, CRM data, Google Ads, etc.
Provides column mapping UI data, fuzzy matching, and join preview.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# COLUMN SIMILARITY
# ---------------------------------------------------------------------------

def column_similarity(col_a: str, col_b: str) -> float:
    """Simple similarity score between two column names (0 to 1)."""
    a = col_a.lower().strip().replace("_", "").replace(" ", "")
    b = col_b.lower().strip().replace("_", "").replace(" ", "")
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.8
    # Jaccard on character bigrams
    def bigrams(s):
        return set(s[i : i + 2] for i in range(len(s) - 1))
    bg_a, bg_b = bigrams(a), bigrams(b)
    if not bg_a or not bg_b:
        return 0.0
    intersection = bg_a & bg_b
    union = bg_a | bg_b
    return len(intersection) / len(union)


def suggest_join_columns(
    df_left: pd.DataFrame,
    df_right: pd.DataFrame,
    threshold: float = 0.5,
) -> List[Dict[str, Any]]:
    """
    Suggest which columns to join on based on name similarity and type compatibility.
    Returns list of suggestions sorted by confidence.
    """
    suggestions = []
    for col_l in df_left.columns:
        for col_r in df_right.columns:
            sim = column_similarity(col_l, col_r)
            if sim < threshold:
                continue
            # Check type compatibility
            type_compat = _types_compatible(df_left[col_l], df_right[col_r])
            score = sim * 0.7 + (0.3 if type_compat else 0.0)
            suggestions.append({
                "left_column": col_l,
                "right_column": col_r,
                "similarity": round(sim, 3),
                "type_compatible": type_compat,
                "confidence": round(score, 3),
            })
    suggestions.sort(key=lambda x: x["confidence"], reverse=True)
    return suggestions


def _types_compatible(series_a: pd.Series, series_b: pd.Series) -> bool:
    """Check if two series have compatible types for joining."""
    a_is_numeric = pd.api.types.is_numeric_dtype(series_a)
    b_is_numeric = pd.api.types.is_numeric_dtype(series_b)
    if a_is_numeric and b_is_numeric:
        return True
    if not a_is_numeric and not b_is_numeric:
        return True
    return False


# ---------------------------------------------------------------------------
# JOIN OPERATIONS
# ---------------------------------------------------------------------------

def join_datasets(
    df_left: pd.DataFrame,
    df_right: pd.DataFrame,
    left_on: str,
    right_on: str,
    how: str = "left",
    suffixes: Tuple[str, str] = ("_left", "_right"),
) -> pd.DataFrame:
    """
    Join two datasets on specified columns.
    how: 'inner', 'left', 'right', 'outer'
    """
    # Coerce join columns to same type
    left_col = df_left[left_on].astype(str).str.strip().str.lower()
    right_col = df_right[right_on].astype(str).str.strip().str.lower()

    df_l = df_left.copy()
    df_r = df_right.copy()
    df_l["_join_key"] = left_col
    df_r["_join_key"] = right_col

    result = pd.merge(
        df_l, df_r,
        on="_join_key",
        how=how,
        suffixes=suffixes,
    )
    result = result.drop(columns=["_join_key"])
    return result


def join_preview(
    df_left: pd.DataFrame,
    df_right: pd.DataFrame,
    left_on: str,
    right_on: str,
    how: str = "left",
    sample_size: int = 10,
) -> Dict[str, Any]:
    """
    Preview a join operation without executing on full dataset.
    Returns stats and sample rows.
    """
    left_keys = set(df_left[left_on].astype(str).str.strip().str.lower())
    right_keys = set(df_right[right_on].astype(str).str.strip().str.lower())
    matched = left_keys & right_keys
    left_only = left_keys - right_keys
    right_only = right_keys - left_keys

    # Execute on sample for preview
    sample_left = df_left.head(sample_size)
    sample_result = join_datasets(sample_left, df_right, left_on, right_on, how)

    return {
        "left_rows": len(df_left),
        "right_rows": len(df_right),
        "left_unique_keys": len(left_keys),
        "right_unique_keys": len(right_keys),
        "matched_keys": len(matched),
        "left_only_keys": len(left_only),
        "right_only_keys": len(right_only),
        "match_rate_left": round(len(matched) / max(len(left_keys), 1) * 100, 1),
        "match_rate_right": round(len(matched) / max(len(right_keys), 1) * 100, 1),
        "sample_matched": list(matched)[:5],
        "sample_left_only": list(left_only)[:5],
        "sample_right_only": list(right_only)[:5],
        "preview_df": sample_result,
    }


def multi_source_merge(
    datasets: Dict[str, pd.DataFrame],
    join_specs: List[Dict],
) -> pd.DataFrame:
    """
    Merge multiple datasets sequentially according to join specifications.
    Each spec: {
        "left": "dataset_name",
        "right": "dataset_name",
        "left_on": "column",
        "right_on": "column",
        "how": "left|inner|right|outer",
    }
    """
    if not join_specs:
        raise ValueError("No join specifications provided")

    first_spec = join_specs[0]
    result = join_datasets(
        datasets[first_spec["left"]],
        datasets[first_spec["right"]],
        first_spec["left_on"],
        first_spec["right_on"],
        first_spec.get("how", "left"),
    )

    for spec in join_specs[1:]:
        right_df = datasets[spec["right"]]
        result = join_datasets(
            result,
            right_df,
            spec["left_on"],
            spec["right_on"],
            spec.get("how", "left"),
        )

    return result


# ---------------------------------------------------------------------------
# DATA COMBINATION (UNION / APPEND)
# ---------------------------------------------------------------------------

def union_datasets(
    datasets: List[pd.DataFrame],
    align_columns: bool = True,
) -> pd.DataFrame:
    """
    Union (vertically stack) multiple datasets.
    If align_columns=True, aligns all columns and fills missing with NaN.
    """
    if not datasets:
        return pd.DataFrame()
    if align_columns:
        return pd.concat(datasets, ignore_index=True, sort=False)
    # Only include common columns
    common_cols = set(datasets[0].columns)
    for df in datasets[1:]:
        common_cols &= set(df.columns)
    common_cols = sorted(common_cols)
    return pd.concat([df[common_cols] for df in datasets], ignore_index=True)


# ---------------------------------------------------------------------------
# AGGREGATION
# ---------------------------------------------------------------------------

def aggregate_data(
    df: pd.DataFrame,
    group_by: List[str],
    agg_columns: Dict[str, str],
) -> pd.DataFrame:
    """
    Aggregate data with flexible grouping.
    agg_columns: {column_name: agg_function} where function is
    'sum', 'mean', 'median', 'min', 'max', 'count', 'first', 'last'
    """
    valid_groups = [c for c in group_by if c in df.columns]
    valid_aggs = {c: fn for c, fn in agg_columns.items() if c in df.columns}
    if not valid_groups or not valid_aggs:
        return df
    return df.groupby(valid_groups, as_index=False).agg(valid_aggs)
