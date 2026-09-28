"""Simulated demonstration dataset.

Writes the fictional P&ID parameter register, the HoQ relationship matrix and
roof, and seeded Monte Carlo measurements for the Taguchi experiment
(inner L9 array of control factors x outer L8 array of noise factors x
replicates). See ``config.DATASET_DISCLOSURE``.
"""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from . import config
from .hoq import HouseOfQuality, relationship_frame, roof_frame
from .orthogonal_arrays import assign_columns, get_array, select_inner_array
from .vor import extract_vor, register_to_frame, weight_vor


# --------------------------------------------------------------------------
# Static tables (register, HoQ)
# --------------------------------------------------------------------------
def build_register() -> pd.DataFrame:
    return register_to_frame(config.PID_REGISTER)


def build_relationships() -> pd.DataFrame:
    return relationship_frame(config.HOQ_RELATIONSHIPS, config.EC_KEYS)


def build_roof() -> pd.DataFrame:
    return roof_frame(config.HOQ_ROOF)


def selected_characteristics(register: pd.DataFrame | None = None) -> list[str]:
    """Characteristics the HoQ selects for optimization (Phases 1-2)."""
    register = build_register() if register is None else register
    vor, _ = weight_vor(extract_vor(register))
    hoq = HouseOfQuality(vor, build_relationships(), build_roof())
    return hoq.select_for_optimization(config.TOP_K_FOR_OPTIMIZATION)


# --------------------------------------------------------------------------
# Measurement simulation model
# --------------------------------------------------------------------------
def _simulate_wall(tol: float, noise: Mapping[str, int], rng: np.random.Generator) -> float:
    p = config.SIMULATION["shell_wall_thickness"]
    nominal = config.CONTROL_FACTORS["shell_wall_thickness"]["nominal_mm"]
    y = nominal + rng.normal(0.0, tol * p["process_sigma_per_tolerance"])
    for name, shift in p["noise_shift"].items():
        y += shift * noise[name]
    return float(y + rng.normal(0.0, p["residual_sigma"]))


def _simulate_bore(tol: float, wall_level: int, noise: Mapping[str, int], rng: np.random.Generator) -> float:
    p = config.SIMULATION["nozzle_bore_position"]
    sigma = tol * p["process_sigma_per_tolerance"]
    dx = (
        rng.normal(0.0, sigma)
        + p["thermal_shift_x"] * noise["thermal_expansion"]
        + p["weld_shift_x"] * noise["weld_distortion"]
        + rng.normal(0.0, p["residual_sigma"])
    )
    dy = (
        rng.normal(0.0, sigma)
        + p["pressure_shift_y"] * noise["pressure_fluctuation"] * (1.0 + p["pressure_shift_wall_coupling"] * wall_level)
        + rng.normal(0.0, p["residual_sigma"])
    )
    return float(np.hypot(dx, dy))


def _simulate_flatness(tol: float, own_level: int, noise: Mapping[str, int], rng: np.random.Generator) -> float:
    p = config.SIMULATION["flange_face_flatness"]
    f = (
        p["mean_fraction_of_tolerance"] * tol
        + rng.normal(0.0, tol * p["process_sigma_per_tolerance"])
        + p["weld_distortion"] * (1.0 + p["weld_distortion_level_coupling"] * own_level) * (noise["weld_distortion"] + 1) / 2.0
        + p["thermal_expansion"] * noise["thermal_expansion"]
        + p["material_scatter"] * noise["material_scatter"]
        + rng.normal(0.0, p["residual_sigma"])
    )
    return float(max(f, p["floor"]))


def simulate_response(
    ec: str,
    levels: Mapping[str, int],
    noise: Mapping[str, int],
    rng: np.random.Generator,
) -> float:
    """One simulated observation of characteristic ``ec``.

    ``levels`` maps each control factor (EC key) to its coded level (0, 1, 2).
    """
    if ec not in config.CONTROL_FACTORS:
        raise ValueError(f"no simulation model for characteristic {ec!r}")
    tol = config.CONTROL_FACTORS[ec]["levels"][levels[ec]]
    if ec == "shell_wall_thickness":
        return _simulate_wall(tol, noise, rng)
    if ec == "nozzle_bore_position":
        return _simulate_bore(tol, levels.get("shell_wall_thickness", 0), noise, rng)
    return _simulate_flatness(tol, levels[ec], noise, rng)


def noise_conditions() -> pd.DataFrame:
    """Outer array: one row per noise condition, noise factors coded -1 / +1."""
    outer = get_array(config.OUTER_ARRAY)[:, list(config.OUTER_ARRAY_COLUMNS)]
    df = pd.DataFrame(np.where(outer == 0, -1, 1), columns=list(config.NOISE_FACTORS))
    df.insert(0, "noise_condition", np.arange(1, len(df) + 1))
    return df


def inner_design(ecs: Sequence[str]) -> tuple[str, pd.DataFrame]:
    """Inner array for control factors ``ecs``: (array name, coded design)."""
    name = select_inner_array(len(ecs), 3)
    cols = assign_columns(name, len(ecs))
    arr = get_array(name)[:, cols]
    design = pd.DataFrame(arr, columns=list(ecs))
    design.index = pd.RangeIndex(1, len(design) + 1, name="run")
    return name, design


def simulate_experiment(
    ecs: Sequence[str],
    design: pd.DataFrame,
    rng: np.random.Generator,
    replicates: int = config.REPLICATES_PER_NOISE_CONDITION,
) -> pd.DataFrame:
    """Long-format measurements: every run x noise condition x replicate."""
    noise = noise_conditions()
    rows = []
    for run, levels_row in design.iterrows():
        levels = {ec: int(levels_row[ec]) for ec in ecs}
        for _, nrow in noise.iterrows():
            ncond = {k: int(nrow[k]) for k in config.NOISE_FACTORS}
            for rep in range(1, replicates + 1):
                rec = {"run": int(run), "noise_condition": int(nrow["noise_condition"]), "replicate": rep}
                for ec in ecs:
                    rec[f"{ec}_level"] = levels[ec]
                    rec[f"{ec}_tolerance_mm"] = config.CONTROL_FACTORS[ec]["levels"][levels[ec]]
                rec.update(ncond)
                for ec in ecs:
                    rec[ec] = simulate_response(ec, levels, ncond, rng)
                rows.append(rec)
    return pd.DataFrame(rows)


def simulate_confirmation(
    ecs: Sequence[str],
    levels: Mapping[str, int],
    seed: int = config.RANDOM_SEED + 1,
    replicates: int = config.REPLICATES_PER_NOISE_CONDITION,
) -> pd.DataFrame:
    """Confirmation experiment at one factor-level combination (fresh seed)."""
    design = pd.DataFrame([[levels[ec] for ec in ecs]], columns=list(ecs))
    design.index = pd.RangeIndex(1, 2, name="run")
    return simulate_experiment(ecs, design, np.random.default_rng(seed), replicates)


def generate_dataset(seed: int = config.RANDOM_SEED) -> dict:
    """Build every raw table of the demonstration dataset (nothing is written)."""
    register = build_register()
    ecs = selected_characteristics(register)
    missing = [ec for ec in ecs if ec not in config.CONTROL_FACTORS]
    if missing:
        raise ValueError(
            f"HoQ selected {missing} for optimization but config.CONTROL_FACTORS has no "
            "factor levels / simulation model for them"
        )
    array_name, design = inner_design(ecs)
    measurements = simulate_experiment(ecs, design, np.random.default_rng(seed))
    return {
        "register": register,
        "relationships": build_relationships(),
        "roof": build_roof(),
        "selected": ecs,
        "inner_array": array_name,
        "measurements": measurements,
    }


def write_dataset(seed: int = config.RANDOM_SEED) -> dict:
    """Generate the dataset and write it to ``data/raw/``."""
    ds = generate_dataset(seed)
    config.DATA_RAW.mkdir(parents=True, exist_ok=True)
    ds["register"].to_csv(config.PID_REGISTER_CSV, index=False)
    ds["relationships"].to_csv(config.HOQ_RELATIONSHIPS_CSV)
    ds["roof"].to_csv(config.HOQ_ROOF_CSV, index=False)
    ds["measurements"].to_csv(config.TAGUCHI_MEASUREMENTS_CSV, index=False, float_format="%.5f")
    return ds
