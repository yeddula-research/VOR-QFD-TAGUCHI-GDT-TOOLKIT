"""Phase 3 orchestration: analyze an inner x outer array experiment.

Each selected characteristic contributes one control factor (its tolerance)
and one response. The optimal level of each factor is the level that gives
the highest mean S/N for that factor's own characteristic.
"""

from __future__ import annotations

from typing import Mapping, Sequence

import pandas as pd

from . import config
from .taguchi import anova, main_effects, predicted_sn, sn_by_run


def design_from_measurements(measurements: pd.DataFrame, ecs: Sequence[str]) -> pd.DataFrame:
    """Coded inner-array design (one row per run) recovered from measurements."""
    cols = [f"{ec}_level" for ec in ecs]
    design = measurements.groupby("run")[cols].first()
    design.columns = list(ecs)
    if (measurements.groupby("run")[cols].nunique() > 1).any().any():
        raise ValueError("factor levels vary within a run")
    return design


def analyze_experiment(
    measurements: pd.DataFrame,
    ecs: Sequence[str],
    control_factors: Mapping = config.CONTROL_FACTORS,
) -> dict:
    """S/N per run, main effects, ANOVA, optimum and predicted S/N for each EC."""
    design = design_from_measurements(measurements, ecs)
    responses = {ec: control_factors[ec]["sn_type"] for ec in ecs}
    sn = sn_by_run(measurements, responses).loc[design.index]
    effects = {ec: main_effects(design, sn[ec]) for ec in ecs}
    anovas = {ec: anova(design, sn[ec]) for ec in ecs}
    optimum = {ec: int(effects[ec][ec].idxmax()) for ec in ecs}
    predicted = {ec: predicted_sn(design, sn[ec], optimum) for ec in ecs}
    optimal_tolerance = {ec: control_factors[ec]["levels"][optimum[ec]] for ec in ecs}
    best_run = {ec: int(sn[ec].idxmax()) for ec in ecs}
    return {
        "design": design,
        "sn": sn,
        "main_effects": effects,
        "anova": anovas,
        "optimum_levels": optimum,
        "optimal_tolerance": optimal_tolerance,
        "predicted_sn": predicted,
        "best_run": best_run,
    }


def confirmation_sn(
    measurements: pd.DataFrame,
    ecs: Sequence[str],
    control_factors: Mapping = config.CONTROL_FACTORS,
) -> dict:
    """Observed S/N of a single-run confirmation experiment."""
    responses = {ec: control_factors[ec]["sn_type"] for ec in ecs}
    sn = sn_by_run(measurements, responses)
    if len(sn) != 1:
        raise ValueError("a confirmation experiment has exactly one run")
    return {ec: float(sn[ec].iloc[0]) for ec in ecs}


def format_level(ec: str, level: int, control_factors: Mapping = config.CONTROL_FACTORS) -> str:
    """Human-readable tolerance for a coded level, e.g. '±0.5 mm'."""
    cf = control_factors[ec]
    return cf["level_format"].format(cf["levels"][level])
