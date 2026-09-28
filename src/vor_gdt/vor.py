"""Phase 1 - Voice of Regulation (VoR) extraction.

Selects the critical-to-quality (CTQ) parameters from a P&ID parameter
register, classifies them by regulatory source, and computes the regulatory
criticality weight of Eq. (1):

    W_r = sum_i(S_i * C_i) / sum_i(C_i)

where S_i is the severity rating of the i-th VoR parameter (1-9), C_i its
compliance criticality index, and n the number of extracted VoR parameters.
"""

from __future__ import annotations

from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from . import config

REGISTER_COLUMNS = [
    "item_id",
    "pid_tag",
    "parameter",
    "value",
    "units",
    "source",
    "severity",
    "compliance_criticality",
]


def register_to_frame(rows: Iterable[tuple] = config.PID_REGISTER) -> pd.DataFrame:
    """Build a register DataFrame from tuples in ``REGISTER_COLUMNS`` order."""
    return pd.DataFrame(list(rows), columns=REGISTER_COLUMNS)


def validate_register(register: pd.DataFrame) -> None:
    """Raise ``ValueError`` if the register is malformed."""
    missing = [c for c in REGISTER_COLUMNS if c not in register.columns]
    if missing:
        raise ValueError(f"register is missing columns: {missing}")
    if register["item_id"].duplicated().any():
        raise ValueError("register item_id values must be unique")
    lo, hi = config.SEVERITY_SCALE
    sev = register["severity"]
    if ((sev < lo) | (sev > hi)).any():
        raise ValueError(f"severity S_i must lie in [{lo}, {hi}]")
    if (register["compliance_criticality"] <= 0).any():
        raise ValueError("compliance criticality C_i must be positive")
    known = set(config.REGULATORY_SOURCES) | set(config.NON_REGULATORY_SOURCES)
    unknown = sorted(set(register["source"]) - known)
    if unknown:
        raise ValueError(f"unknown source codes: {unknown}")


def extract_vor(
    register: pd.DataFrame,
    regulatory_sources: Mapping[str, str] = config.REGULATORY_SOURCES,
) -> pd.DataFrame:
    """Return the VoR (CTQ) parameters: register items with a regulatory source.

    The returned frame keeps register order and adds ``source_name`` (the full
    name of the regulatory source).
    """
    validate_register(register)
    vor = register[register["source"].isin(regulatory_sources.keys())].copy()
    vor["source_name"] = vor["source"].map(regulatory_sources)
    return vor.reset_index(drop=True)


def regulatory_criticality_weight(severity, criticality) -> float:
    """Eq. (1): W_r = sum(S_i * C_i) / sum(C_i)."""
    s = np.asarray(severity, dtype=float)
    c = np.asarray(criticality, dtype=float)
    if s.shape != c.shape or s.size == 0:
        raise ValueError("severity and criticality must be non-empty and the same length")
    if np.any(c <= 0):
        raise ValueError("compliance criticality C_i must be positive")
    return float(np.sum(s * c) / np.sum(c))


def parameter_weights(severity, criticality) -> np.ndarray:
    """Per-parameter weights W_r,i used in Eq. (2).

    Eq. (1) produces a single aggregate W_r, while Eq. (2) needs one weight per
    VoR parameter. This toolkit uses each parameter's own term of the Eq. (1)
    sum, W_r,i = S_i * C_i / sum(C), so that sum_i W_r,i equals W_r exactly.
    """
    s = np.asarray(severity, dtype=float)
    c = np.asarray(criticality, dtype=float)
    if s.shape != c.shape or s.size == 0:
        raise ValueError("severity and criticality must be non-empty and the same length")
    if np.any(c <= 0):
        raise ValueError("compliance criticality C_i must be positive")
    return s * c / np.sum(c)


def weight_vor(vor: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Add ``weight`` (W_r,i) to the VoR frame and return it with aggregate W_r."""
    out = vor.copy()
    out["weight"] = parameter_weights(out["severity"], out["compliance_criticality"])
    w_r = regulatory_criticality_weight(out["severity"], out["compliance_criticality"])
    return out, w_r


def summarize_by_source(vor: pd.DataFrame) -> pd.DataFrame:
    """Count VoR parameters and sum their weights per regulatory source."""
    if "weight" not in vor.columns:
        vor, _ = weight_vor(vor)
    return (
        vor.groupby("source_name", sort=True)
        .agg(parameters=("item_id", "count"), total_weight=("weight", "sum"))
        .reset_index()
    )
