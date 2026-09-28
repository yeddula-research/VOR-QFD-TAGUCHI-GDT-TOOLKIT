"""Traceability mapping: GD&T callout <-> HoQ characteristic <-> VoR <-> P&ID.

Every callout in the GD&T scheme is traced back through the HoQ relationship
matrix to the VoR parameters (and their P&ID tags and regulatory sources)
that drive it, and every VoR parameter is checked for at least one
downstream callout.
"""

from __future__ import annotations

import pandas as pd

from . import config


def build_traceability_matrix(
    scheme: pd.DataFrame,
    vor: pd.DataFrame,
    relationships: pd.DataFrame,
    threshold: int = config.TRACE_RELATIONSHIP_THRESHOLD,
) -> pd.DataFrame:
    """One row per (callout, VoR parameter) link with R_ij >= ``threshold``."""
    vor_idx = vor.set_index("item_id")
    rows = []
    for _, s in scheme.iterrows():
        ec = s["ec"]
        linked = relationships.index[relationships[ec] >= threshold]
        for item_id in linked:
            v = vor_idx.loc[item_id]
            rows.append(
                {
                    "callout": s["callout"],
                    "control": s["control"],
                    "ec": ec,
                    "engineering_characteristic": s["engineering_characteristic"],
                    "priority_rank": s["priority_rank"],
                    "relationship": int(relationships.loc[item_id, ec]),
                    "vor_item": item_id,
                    "vor_parameter": v["parameter"],
                    "pid_tag": v["pid_tag"],
                    "regulatory_source": v["source_name"],
                }
            )
    return pd.DataFrame(rows)


def coverage(trace: pd.DataFrame, scheme: pd.DataFrame, vor: pd.DataFrame) -> dict:
    """Coverage of the traceability matrix in both directions.

    Returns the share of VoR parameters that reach at least one callout, the
    share of callouts that trace to at least one VoR parameter, and the IDs /
    characteristics left untraced.
    """
    vor_ids = set(vor["item_id"])
    traced_vor = set(trace["vor_item"]) if len(trace) else set()
    ecs = set(scheme["ec"])
    traced_ecs = set(trace["ec"]) if len(trace) else set()
    return {
        "vor_parameters": len(vor_ids),
        "vor_parameters_traced": len(traced_vor & vor_ids),
        "vor_coverage_pct": 100.0 * len(traced_vor & vor_ids) / len(vor_ids) if vor_ids else 0.0,
        "callouts": len(ecs),
        "callouts_traced": len(traced_ecs & ecs),
        "callout_coverage_pct": 100.0 * len(traced_ecs & ecs) / len(ecs) if ecs else 0.0,
        "untraced_vor": sorted(vor_ids - traced_vor),
        "untraced_callouts": sorted(ecs - traced_ecs),
    }
