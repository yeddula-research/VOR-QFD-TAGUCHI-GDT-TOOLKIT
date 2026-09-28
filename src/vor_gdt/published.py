"""The paper's published results, recorded for side-by-side checking.

Tables 1-3 below are copied exactly as printed in the ICCBI-2026 proceedings
(pp. 496-498). They are reference data: nothing in the demonstration pipeline
is fitted to them. The helpers below only run consistency checks and a
main-effects analysis on the published Table 2 values, so that a reader can
confirm the paper's reported optimum directly from its own table.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .orthogonal_arrays import get_array
from .taguchi import main_effects

SOURCE = (
    "Yeddula, Adurthy, Shaikh, ICCBI-2026 proceedings, pp. 492-499, "
    "ISBN 979-8-3315-6379-0"
)

# Table 1 - House of Quality: AIC rankings of engineering characteristics (p. 496).
TABLE1 = pd.DataFrame(
    [
        ("Shell wall thickness tolerance", "Design pressure, corrosion allowance, hydrotest rating", 27, 94.6, 1),
        ("Nozzle bore positional tolerance", "Flow rate, instrumentation tap location, interlock clearance", 24, 88.3, 2),
        ("Flange face flatness", "Gasket seating, pressure boundary integrity, bolt load distribution", 21, 81.7, 3),
        ("Surface roughness (Ra)", "Corrosion rate, coating adhesion", 15, 58.2, 4),
        ("Shell out-of-roundness", "Structural stability, external pressure rating", 12, 47.9, 5),
        ("Weld joint perpendicularity", "Assembly alignment, radiographic inspection access", 9, 34.1, 6),
    ],
    columns=["Engineering characteristic", "VoR parameters influenced", "Relationship sum", "Wr-weighted AIC", "Priority rank"],
)

# Table 2 - Taguchi L9 orthogonal array: S/N ratio results for top three characteristics (p. 496).
TABLE2 = pd.DataFrame(
    [
        ("Run 1", 0.5, 0.3, 0.05, 18.2, 16.4, 20.1),
        ("Run 2", 0.5, 0.5, 0.10, 17.8, 14.9, 17.3),
        ("Run 3", 0.5, 0.8, 0.15, 17.1, 12.6, 14.8),
        ("Run 4", 0.8, 0.3, 0.10, 15.6, 16.1, 17.0),
        ("Run 5", 0.8, 0.5, 0.15, 15.2, 14.3, 14.5),
        ("Run 6", 0.8, 0.8, 0.05, 15.9, 12.4, 20.0),
        ("Run 7", 1.2, 0.3, 0.15, 12.3, 15.8, 14.2),
        ("Run 8", 1.2, 0.5, 0.05, 12.8, 14.0, 19.8),
        ("Run 9", 1.2, 0.8, 0.10, 11.9, 11.8, 17.1),
        ("Optimal", 0.5, 0.3, 0.05, 18.2, 16.4, 20.1),
    ],
    columns=[
        "Experiment run",
        "Wall thickness tolerance (mm)",
        "Bore position tolerance (mm)",
        "Flange flatness (mm)",
        "S/N ratio — wall (dB)",
        "S/N ratio — bore (dB)",
        "S/N ratio — flatness (dB)",
    ],
)

# Table 3 - Quantitative benchmarking against conventional design methods (p. 498).
TABLE3 = pd.DataFrame(
    [
        ("Conventional Design Method", 31, 28, "Moderate"),
        ("QFD-Based Design", 18, 15, "Improved"),
        ("Proposed VoR–QFD–Taguchi–GD&T Framework", 9, 6, "High"),
    ],
    columns=["Design Approach", "Rework Rate (%)", "Dimensional Non-Conformance (%)", "Design Robustness"],
)

# Table 2 prints the wall and bore tolerances as "±" values; they are stored
# here as their magnitudes and restored by table2_as_printed().
TABLE2_FACTORS = {
    "Wall thickness tolerance": "Wall thickness tolerance (mm)",
    "Bore position tolerance": "Bore position tolerance (mm)",
    "Flange flatness": "Flange flatness (mm)",
}
TABLE2_RESPONSES = {
    "Wall thickness tolerance": "S/N ratio — wall (dB)",
    "Bore position tolerance": "S/N ratio — bore (dB)",
    "Flange flatness": "S/N ratio — flatness (dB)",
}
_PLUS_MINUS_COLUMNS = ("Wall thickness tolerance (mm)", "Bore position tolerance (mm)")


def table2_as_printed() -> pd.DataFrame:
    """Table 2 formatted as printed in the paper (± tolerances, one-decimal S/N)."""
    out = TABLE2.copy().astype(object)
    for col in _PLUS_MINUS_COLUMNS:
        out[col] = TABLE2[col].map(lambda v: f"±{v:.1f}")
    out["Flange flatness (mm)"] = TABLE2["Flange flatness (mm)"].map(lambda v: f"{v:.2f}")
    for col in TABLE2_RESPONSES.values():
        out[col] = TABLE2[col].map(lambda v: f"{v:.1f}")
    return out


def table2_runs() -> pd.DataFrame:
    """The nine experiment runs of Table 2 (without the 'Optimal' summary row)."""
    return TABLE2[TABLE2["Experiment run"].str.startswith("Run")].reset_index(drop=True)


def table2_design() -> pd.DataFrame:
    """Coded design (levels 0, 1, 2 from tightest to loosest) of Table 2's runs."""
    runs = table2_runs()
    design = {}
    for factor, col in TABLE2_FACTORS.items():
        levels = sorted(runs[col].unique())
        design[factor] = runs[col].map({v: i for i, v in enumerate(levels)}).to_numpy()
    return pd.DataFrame(design)


def table2_is_l9() -> bool:
    """True if Table 2's three factor columns are columns 1-3 of the standard L9 array."""
    return bool(np.array_equal(table2_design().to_numpy(), get_array("L9")[:, :3]))


def table2_main_effects() -> pd.DataFrame:
    """Mean published S/N at each level of each factor, for that factor's own characteristic."""
    runs = table2_runs()
    design = table2_design()
    rows = []
    for factor, col in TABLE2_FACTORS.items():
        me = main_effects(design[[factor]], runs[TABLE2_RESPONSES[factor]])
        levels = sorted(runs[col].unique())
        for level, value in me[factor].items():
            rows.append(
                {
                    "Factor": factor,
                    "Level": int(level) + 1,
                    "Tolerance (mm)": levels[int(level)],
                    "Mean published S/N (dB)": float(value),
                }
            )
    return pd.DataFrame(rows)


def table2_optimum() -> dict:
    """Tolerance at the level with the highest mean published S/N, per factor."""
    me = table2_main_effects()
    best = me.loc[me.groupby("Factor", sort=False)["Mean published S/N (dB)"].idxmax()]
    return dict(zip(best["Factor"], best["Tolerance (mm)"]))


def table2_reported_optimum() -> dict:
    """The 'Optimal' row as printed in Table 2."""
    row = TABLE2[TABLE2["Experiment run"] == "Optimal"].iloc[0]
    return {factor: float(row[col]) for factor, col in TABLE2_FACTORS.items()}


def table1_ranks_follow_aic() -> bool:
    """True if Table 1's priority ranks follow its Wr-weighted AIC order."""
    order = TABLE1.sort_values("Wr-weighted AIC", ascending=False)["Priority rank"].tolist()
    return order == list(range(1, len(TABLE1) + 1))
