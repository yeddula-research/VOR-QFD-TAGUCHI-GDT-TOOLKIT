"""Phase 4 - GD&T scheme formulation (ASME Y14.5-2018).

Maps each engineering characteristic to a GD&T control type, attaches a
datum reference frame, and renders feature control frames with the tolerance
values from Phase 3 (optimized characteristics) or the configured defaults
(characteristics that are specified but not optimized).

Note: ASME Y14.5-2018 removed the concentricity and symmetry characteristics
that appeared in earlier editions; they are therefore not offered here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

import pandas as pd

from . import config

# Geometric characteristics of ASME Y14.5-2018: category, symbol, and whether
# a datum reference is required ("required"), not permitted ("none"), or
# optional ("optional").
GEOMETRIC_CHARACTERISTICS = {
    "straightness": ("form", "⏤", "none"),
    "flatness": ("form", "⏥", "none"),
    "circularity": ("form", "○", "none"),
    "cylindricity": ("form", "⌭", "none"),
    "profile_of_a_line": ("profile", "⌒", "optional"),
    "profile_of_a_surface": ("profile", "⌓", "optional"),
    "angularity": ("orientation", "∠", "required"),
    "perpendicularity": ("orientation", "⟂", "required"),
    "parallelism": ("orientation", "∥", "required"),
    "position": ("location", "⌖", "required"),
    "circular_runout": ("runout", "↗", "required"),
    "total_runout": ("runout", "⌰", "required"),
}

REMOVED_IN_2018 = {"concentricity", "symmetry"}

# Non-geometric specifications that still appear in the scheme.
OTHER_CONTROLS = {
    "size": "Size dimension with ± tolerance (ASME Y14.5-2018)",
    "surface_texture": "Surface texture Ra (symbol per ASME Y14.36; not a Y14.5 geometric control)",
}


@dataclass(frozen=True)
class FeatureControlFrame:
    """A single GD&T callout."""

    characteristic: str
    tolerance: float
    datums: Sequence[str] = field(default_factory=tuple)
    diameter_zone: bool = False
    nominal: float | None = None
    units: str = "mm"

    def __post_init__(self) -> None:
        if self.characteristic in REMOVED_IN_2018:
            raise ValueError(f"{self.characteristic} is not a characteristic in ASME Y14.5-2018")
        if self.characteristic not in GEOMETRIC_CHARACTERISTICS and self.characteristic not in OTHER_CONTROLS:
            raise ValueError(f"unknown control {self.characteristic!r}")
        if self.tolerance <= 0:
            raise ValueError("tolerance must be positive")
        rule = GEOMETRIC_CHARACTERISTICS.get(self.characteristic, (None, None, "none"))[2]
        if rule == "none" and self.datums:
            raise ValueError(f"{self.characteristic} is a form control and cannot reference datums")
        if rule == "required" and not self.datums:
            raise ValueError(f"{self.characteristic} requires a datum reference")
        if self.characteristic == "size" and self.nominal is None:
            raise ValueError("a size callout needs a nominal value")

    @property
    def category(self) -> str:
        if self.characteristic in GEOMETRIC_CHARACTERISTICS:
            return GEOMETRIC_CHARACTERISTICS[self.characteristic][0]
        return self.characteristic

    def render(self) -> str:
        """Plain-text rendering, e.g. ``⌖ | ⌀0.60 | A | B | C``."""
        if self.characteristic == "size":
            return f"{self.nominal:.1f} ±{self.tolerance:.2f} {self.units}"
        if self.characteristic == "surface_texture":
            return f"Ra {self.tolerance:.1f} µm max"
        symbol = GEOMETRIC_CHARACTERISTICS[self.characteristic][1]
        zone = ("⌀" if self.diameter_zone else "") + f"{self.tolerance:.2f}"
        return " | ".join([symbol, zone, *self.datums])


def position_zone_diameter(radial_tolerance: float) -> float:
    """Diameter of a cylindrical position zone for a radial allowance of ±r.

    A bore axis allowed to lie within r of true position occupies a
    cylindrical zone of diameter 2r.
    """
    if radial_tolerance <= 0:
        raise ValueError("radial tolerance must be positive")
    return 2.0 * radial_tolerance


def build_callout(ec: str, tolerance: float, mapping: Mapping = config.GDT_MAPPING) -> FeatureControlFrame:
    """Feature control frame for characteristic ``ec`` at ``tolerance``."""
    m = mapping[ec]
    control = m["control"]
    datums = tuple(m["datums"])
    if control == "position":
        return FeatureControlFrame("position", position_zone_diameter(tolerance), datums, diameter_zone=True)
    if control == "size":
        nominal = config.CONTROL_FACTORS[ec]["nominal_mm"]
        return FeatureControlFrame("size", tolerance, datums, nominal=nominal)
    if control == "surface_texture":
        return FeatureControlFrame("surface_texture", tolerance, datums, units="um")
    return FeatureControlFrame(control, tolerance, datums)


def formulate_scheme(
    ranking: pd.DataFrame,
    optimal_tolerances: Mapping[str, float],
    mapping: Mapping = config.GDT_MAPPING,
) -> pd.DataFrame:
    """GD&T scheme for every engineering characteristic in ``ranking``.

    Optimized characteristics use their Phase 3 optimal tolerance; the others
    use their configured default.
    """
    rows = []
    for _, r in ranking.iterrows():
        ec = r["ec"]
        optimized = ec in optimal_tolerances
        tol = optimal_tolerances[ec] if optimized else mapping[ec]["default_tolerance"]
        if tol is None:
            raise ValueError(f"{ec} was not optimized and has no default tolerance")
        fcf = build_callout(ec, tol, mapping)
        rows.append(
            {
                "priority_rank": int(r["priority_rank"]),
                "ec": ec,
                "engineering_characteristic": r["engineering_characteristic"],
                "aic": r["aic"],
                "control": fcf.characteristic,
                "category": fcf.category,
                "datums": "|".join(fcf.datums) if fcf.datums else "-",
                "tolerance_source": "Taguchi optimum" if optimized else "Default (not optimized)",
                "callout": fcf.render(),
            }
        )
    return pd.DataFrame(rows)
