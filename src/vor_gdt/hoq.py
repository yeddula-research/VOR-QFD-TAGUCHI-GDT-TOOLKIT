"""Phase 2 - QFD requirement prioritization with a House of Quality (HoQ).

Rows are VoR parameters (weighted by W_r,i from Phase 1); columns are
engineering characteristics (ECs). The relationship matrix holds scores
R_ij in {0, 1, 3, 9}, and the absolute importance of each EC is Eq. (2):

    AIC_j = sum_{i=1..m} W_r,i * R_ij

The HoQ roof records technical correlations between ECs so that conflicts
can be reconciled during optimization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from . import config


def relationship_frame(
    relationships: dict = config.HOQ_RELATIONSHIPS,
    ec_keys: Sequence[str] = config.EC_KEYS,
) -> pd.DataFrame:
    """Relationship matrix as a DataFrame indexed by VoR item_id."""
    df = pd.DataFrame.from_dict(relationships, orient="index", columns=list(ec_keys))
    df.index.name = "item_id"
    return df


def roof_frame(roof: Iterable[tuple] = config.HOQ_ROOF) -> pd.DataFrame:
    """Roof correlations as a long DataFrame (ec_a, ec_b, correlation)."""
    return pd.DataFrame(list(roof), columns=["ec_a", "ec_b", "correlation"])


def absolute_importance(weights, relationships) -> np.ndarray:
    """Eq. (2): AIC_j = sum_i W_r,i * R_ij for every column j."""
    w = np.asarray(weights, dtype=float)
    r = np.asarray(relationships, dtype=float)
    if r.ndim != 2 or r.shape[0] != w.shape[0]:
        raise ValueError("relationships must be (m VoR parameters x n ECs) with m == len(weights)")
    return w @ r


@dataclass
class HouseOfQuality:
    """A House of Quality built from weighted VoR parameters.

    Parameters
    ----------
    vor:
        Weighted VoR frame from :func:`vor_gdt.vor.weight_vor` (needs
        ``item_id``, ``parameter`` and ``weight``).
    relationships:
        Relationship matrix indexed by ``item_id`` with one column per EC.
    roof:
        Optional roof correlations (``ec_a``, ``ec_b``, ``correlation``).
    ec_labels:
        Display names for the EC columns.
    """

    vor: pd.DataFrame
    relationships: pd.DataFrame
    roof: pd.DataFrame = field(default_factory=lambda: roof_frame([]))
    ec_labels: dict = field(default_factory=lambda: dict(config.EC_LABELS))

    def __post_init__(self) -> None:
        allowed = set(config.RELATIONSHIP_SCALE)
        values = set(np.unique(self.relationships.to_numpy()).tolist())
        if not values <= allowed:
            raise ValueError(f"relationship scores must be in {sorted(allowed)}, got {sorted(values)}")
        vor_ids = list(self.vor["item_id"])
        missing = [i for i in vor_ids if i not in self.relationships.index]
        extra = [i for i in self.relationships.index if i not in vor_ids]
        if missing or extra:
            raise ValueError(f"HoQ rows must match VoR parameters (missing={missing}, extra={extra})")
        self.relationships = self.relationships.loc[vor_ids]
        for col in ("ec_a", "ec_b"):
            unknown = set(self.roof[col]) - set(self.relationships.columns)
            if unknown:
                raise ValueError(f"roof references unknown ECs: {sorted(unknown)}")

    @property
    def ec_keys(self) -> list[str]:
        return list(self.relationships.columns)

    def absolute_importance(self) -> pd.Series:
        """AIC_j for every engineering characteristic (Eq. 2)."""
        aic = absolute_importance(self.vor["weight"].to_numpy(), self.relationships.to_numpy())
        return pd.Series(aic, index=self.ec_keys, name="aic")

    def relationship_sums(self) -> pd.Series:
        """Unweighted column sums of R_ij."""
        return self.relationships.sum(axis=0).rename("relationship_sum")

    def influencing_vor(self, ec: str, threshold: int = 9) -> list[str]:
        """VoR parameter names whose R_ij for ``ec`` is at least ``threshold``."""
        mask = self.relationships[ec] >= threshold
        ids = list(self.relationships.index[mask])
        names = self.vor.set_index("item_id").loc[ids, "parameter"]
        return list(names)

    def ranking(self) -> pd.DataFrame:
        """ECs ranked by AIC (1 = highest), with relative importance in %."""
        aic = self.absolute_importance()
        df = pd.DataFrame(
            {
                "ec": self.ec_keys,
                "engineering_characteristic": [self.ec_labels.get(k, k) for k in self.ec_keys],
                "vor_parameters_strong": ["; ".join(self.influencing_vor(k, 9)) for k in self.ec_keys],
                "relationship_sum": self.relationship_sums().to_numpy(),
                "aic": aic.to_numpy(),
            }
        )
        df["relative_importance_pct"] = 100.0 * df["aic"] / df["aic"].sum()
        df = df.sort_values("aic", ascending=False, kind="mergesort").reset_index(drop=True)
        df["priority_rank"] = np.arange(1, len(df) + 1)
        return df

    def select_for_optimization(self, top_k: int = config.TOP_K_FOR_OPTIMIZATION) -> list[str]:
        """The ``top_k`` highest-AIC characteristics (Phase 3 candidates)."""
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        return list(self.ranking()["ec"].head(top_k))

    def conflicts(self, ecs: Sequence[str] | None = None) -> pd.DataFrame:
        """Negative roof correlations, optionally restricted to pairs touching ``ecs``."""
        neg = self.roof[self.roof["correlation"] < 0]
        if ecs is not None:
            keep = set(ecs)
            neg = neg[neg["ec_a"].isin(keep) | neg["ec_b"].isin(keep)]
        return neg.reset_index(drop=True)
