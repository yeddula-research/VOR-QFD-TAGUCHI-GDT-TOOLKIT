"""Phase 3 - Taguchi robust design and tolerance optimization.

Signal-to-noise (S/N) ratios, main effects, optimal factor levels, additive
prediction of the optimal S/N, and ANOVA percentage contributions.

Eq. (3), nominal-the-best:

    eta = 10 * log10( ybar^2 / s^2 )

where ybar is the mean response across the noise conditions of one run and
s^2 its variance. The paper's printed Eq. (3) renders the numerator as
"y^-2"; its Figure 1 gives the standard form ybar^2 / s^2, which is what is
implemented here. Smaller-the-better and larger-the-better forms are included
for characteristics whose ideal value is zero or as large as possible.
"""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np
import pandas as pd
from scipy import stats

SN_TYPES = ("nominal_the_best", "smaller_the_better", "larger_the_better")


def sn_nominal_the_best(y) -> float:
    """Eq. (3): 10*log10(ybar^2 / s^2), with s^2 the sample variance (ddof=1)."""
    y = np.asarray(y, dtype=float)
    if y.size < 2:
        raise ValueError("nominal-the-best S/N needs at least two observations")
    s2 = np.var(y, ddof=1)
    if s2 <= 0:
        raise ValueError("variance is zero; S/N is unbounded")
    return float(10.0 * np.log10(np.mean(y) ** 2 / s2))


def sn_smaller_the_better(y) -> float:
    """-10*log10(mean(y^2))."""
    y = np.asarray(y, dtype=float)
    if y.size < 1:
        raise ValueError("need at least one observation")
    msd = np.mean(y**2)
    if msd <= 0:
        raise ValueError("mean square is zero; S/N is unbounded")
    return float(-10.0 * np.log10(msd))


def sn_larger_the_better(y) -> float:
    """-10*log10(mean(1/y^2))."""
    y = np.asarray(y, dtype=float)
    if y.size < 1:
        raise ValueError("need at least one observation")
    if np.any(y == 0):
        raise ValueError("larger-the-better S/N is undefined for zero responses")
    return float(-10.0 * np.log10(np.mean(1.0 / y**2)))


def sn_ratio(y, sn_type: str) -> float:
    """Dispatch to the S/N form named by ``sn_type``."""
    if sn_type == "nominal_the_best":
        return sn_nominal_the_best(y)
    if sn_type == "smaller_the_better":
        return sn_smaller_the_better(y)
    if sn_type == "larger_the_better":
        return sn_larger_the_better(y)
    raise ValueError(f"unknown sn_type {sn_type!r}; choose from {SN_TYPES}")


def sn_by_run(
    measurements: pd.DataFrame,
    responses: Mapping[str, str],
    run_col: str = "run",
) -> pd.DataFrame:
    """S/N ratio of each response for each run.

    ``responses`` maps a response column in ``measurements`` to its S/N type.
    Returns one row per run, one column per response.
    """
    out = {}
    for col, kind in responses.items():
        out[col] = measurements.groupby(run_col)[col].apply(lambda s, k=kind: sn_ratio(s.to_numpy(), k))
    return pd.DataFrame(out)


def main_effects(design: pd.DataFrame, response: Sequence[float]) -> pd.DataFrame:
    """Mean response at each level of each factor.

    ``design`` has one column per factor with coded levels (0, 1, 2, ...).
    Returns a frame indexed by level with one column per factor.
    """
    y = np.asarray(response, dtype=float)
    if len(design) != y.size:
        raise ValueError("design and response lengths differ")
    effects = {}
    for factor in design.columns:
        effects[factor] = pd.Series(y).groupby(design[factor].to_numpy()).mean()
    df = pd.DataFrame(effects)
    df.index.name = "level"
    return df


def optimal_levels(design: pd.DataFrame, response: Sequence[float]) -> dict:
    """Level of each factor with the highest mean S/N (higher S/N = more robust)."""
    me = main_effects(design, response)
    return {factor: int(me[factor].idxmax()) for factor in me.columns}


def predicted_sn(design: pd.DataFrame, response: Sequence[float], levels: Mapping[str, int]) -> float:
    """Additive-model prediction: grand mean + sum of (level mean - grand mean)."""
    y = np.asarray(response, dtype=float)
    me = main_effects(design, y)
    grand = y.mean()
    return float(grand + sum(me.loc[levels[f], f] - grand for f in levels))


def anova(design: pd.DataFrame, response: Sequence[float]) -> pd.DataFrame:
    """ANOVA of ``response`` over the factors in ``design``.

    Returns columns: source, dof, sum_sq, mean_sq, F, p_value,
    contribution_pct. The residual (unassigned columns and error) is reported
    as "Error"; percentage contribution is SS_factor / SS_total * 100.
    """
    y = np.asarray(response, dtype=float)
    n = y.size
    if len(design) != n:
        raise ValueError("design and response lengths differ")
    grand = y.mean()
    ss_total = float(np.sum((y - grand) ** 2))
    rows = []
    for factor in design.columns:
        levels = design[factor].to_numpy()
        ss = 0.0
        for lvl in np.unique(levels):
            mask = levels == lvl
            ss += mask.sum() * (y[mask].mean() - grand) ** 2
        rows.append({"source": factor, "dof": len(np.unique(levels)) - 1, "sum_sq": float(ss)})
    ss_factors = sum(r["sum_sq"] for r in rows)
    dof_factors = sum(r["dof"] for r in rows)
    dof_error = n - 1 - dof_factors
    if dof_error < 0:
        raise ValueError("more factor degrees of freedom than runs allow")
    ss_error = max(ss_total - ss_factors, 0.0)
    ms_error = ss_error / dof_error if dof_error > 0 else np.nan
    for r in rows:
        r["mean_sq"] = r["sum_sq"] / r["dof"]
        if dof_error > 0 and ms_error > 0:
            r["F"] = r["mean_sq"] / ms_error
            r["p_value"] = float(stats.f.sf(r["F"], r["dof"], dof_error))
        else:
            r["F"] = np.nan
            r["p_value"] = np.nan
    rows.append(
        {"source": "Error", "dof": dof_error, "sum_sq": ss_error, "mean_sq": ms_error, "F": np.nan, "p_value": np.nan}
    )
    rows.append({"source": "Total", "dof": n - 1, "sum_sq": ss_total, "mean_sq": np.nan, "F": np.nan, "p_value": np.nan})
    df = pd.DataFrame(rows, columns=["source", "dof", "sum_sq", "mean_sq", "F", "p_value"])
    df["contribution_pct"] = 100.0 * df["sum_sq"] / ss_total if ss_total > 0 else np.nan
    return df
