"""
Safe Formula Engine -- AST-based arithmetic evaluator.
Supports column references, safe functions, and DAX-like syntax.
No eval(), no exec(), no Function() -- pure arithmetic only.
"""
import ast
import math
import operator
import re
import logging
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SAFE FUNCTIONS
# ---------------------------------------------------------------------------

SAFE_FUNCS = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "pow": pow,
    "floor": math.floor,
    "ceil": math.ceil,
    "exp": math.exp,
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


# ---------------------------------------------------------------------------
# AST-BASED SAFE EVALUATOR (SCALAR)
# ---------------------------------------------------------------------------

def _safe_eval_node(node: ast.AST, context: Dict[str, float]) -> float:
    """Recursively evaluate an AST node using only approved operations."""
    if isinstance(node, ast.Expression):
        return _safe_eval_node(node.body, context)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Name):
        key = node.id.lower()
        if key in context:
            return float(context[key])
        raise ValueError(f"Unknown variable: {node.id}")
    if isinstance(node, ast.BinOp):
        op_fn = _OPERATORS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        left = _safe_eval_node(node.left, context)
        right = _safe_eval_node(node.right, context)
        if isinstance(node.op, ast.Div) and right == 0:
            return 0.0
        return float(op_fn(left, right))
    if isinstance(node, ast.UnaryOp):
        op_fn = _OPERATORS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return float(op_fn(_safe_eval_node(node.operand, context)))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in SAFE_FUNCS:
            raise ValueError(f"Unsupported function: {ast.dump(node.func)}")
        fn = SAFE_FUNCS[node.func.id]
        args = [_safe_eval_node(a, context) for a in node.args]
        if node.func.id == "round" and len(args) > 1:
            args[1] = int(args[1])
        return float(fn(*args))
    raise ValueError(f"Unsupported expression: {type(node).__name__}")


def evaluate_formula(
    formula: str,
    context: Dict[str, float],
    raise_errors: bool = False,
) -> float:
    """Safely evaluate an arithmetic formula with column references."""
    try:
        normalized = formula.strip()
        tree = ast.parse(normalized, mode="eval")
        return _safe_eval_node(tree, context)
    except ZeroDivisionError:
        return 0.0
    except Exception as e:
        if raise_errors:
            raise
        log.debug(f"Formula eval error: {e}")
        return float("nan")


# ---------------------------------------------------------------------------
# DATAFRAME-LEVEL FORMULA APPLICATION
# ---------------------------------------------------------------------------

def _safe_divide_series(a: pd.Series, b: pd.Series) -> pd.Series:
    """Divide two series, returning 0 where denominator is 0."""
    return np.where(b != 0, a / b, 0.0)


def apply_formula_to_df(
    df: pd.DataFrame,
    formula: str,
    result_column: str = "result",
) -> pd.Series:
    """
    Apply a formula to every row of a DataFrame.
    Column names in the formula are matched case-insensitively to df columns.
    Returns a Series with the results.
    """
    col_map = {c.lower(): c for c in df.columns}
    results = []
    for _, row in df.iterrows():
        ctx = {}
        for col in df.columns:
            try:
                ctx[col.lower()] = float(row[col])
            except (ValueError, TypeError):
                ctx[col.lower()] = 0.0
        results.append(evaluate_formula(formula, ctx))
    return pd.Series(results, index=df.index, name=result_column)


def bulk_apply_metrics(
    df: pd.DataFrame,
    metrics: List[Dict],
) -> pd.DataFrame:
    """
    Apply multiple metric formulas to a DataFrame.
    Each metric dict must have 'id' and 'formula' keys.
    Returns a new DataFrame with the original + computed columns.
    """
    result = df.copy()
    available_cols = set(c.lower() for c in df.columns)
    for metric in metrics:
        required = set(metric.get("required_columns", []))
        if not required.issubset(available_cols):
            continue
        try:
            result[metric["id"]] = apply_formula_to_df(df, metric["formula"])
        except Exception as e:
            log.warning(f"Failed to compute {metric['id']}: {e}")
    return result


def validate_formula(formula: str) -> Optional[str]:
    """Validate a formula. Returns None if valid, error message if invalid."""
    try:
        tree = ast.parse(formula.strip(), mode="eval")
        _check_node_safety(tree)
        return None
    except SyntaxError as e:
        return f"Syntax error: {e}"
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"Invalid formula: {e}"


def _check_node_safety(node: ast.AST) -> None:
    """Check that an AST node only contains safe operations."""
    if isinstance(node, ast.Expression):
        _check_node_safety(node.body)
    elif isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise ValueError(f"Only numbers allowed, got {type(node.value).__name__}")
    elif isinstance(node, ast.Name):
        pass  # Column references are ok
    elif isinstance(node, ast.BinOp):
        if type(node.op) not in _OPERATORS:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        _check_node_safety(node.left)
        _check_node_safety(node.right)
    elif isinstance(node, ast.UnaryOp):
        if type(node.op) not in _OPERATORS:
            raise ValueError(f"Unsupported unary operator")
        _check_node_safety(node.operand)
    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls allowed")
        if node.func.id not in SAFE_FUNCS:
            raise ValueError(f"Unknown function: {node.func.id}. Allowed: {', '.join(SAFE_FUNCS)}")
        if node.keywords:
            raise ValueError("Keyword arguments are not supported in formulas")
        for a in node.args:
            _check_node_safety(a)
    else:
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")


def extract_variables(formula: str) -> List[str]:
    """Extract all variable (column) names referenced in a formula."""
    try:
        tree = ast.parse(formula.strip(), mode="eval")
    except SyntaxError:
        return []
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id not in SAFE_FUNCS:
            names.append(node.id)
    return sorted(set(names))
