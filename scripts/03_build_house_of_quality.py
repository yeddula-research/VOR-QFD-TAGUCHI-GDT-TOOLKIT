"""Step 3 - Phase 2: House of Quality prioritization (Eq. 2) -> Table 1."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from vor_gdt import config  # noqa: E402
from vor_gdt.hoq import HouseOfQuality  # noqa: E402
from vor_gdt.reporting import write_json, write_table  # noqa: E402


def main() -> None:
    vor = pd.read_csv(config.DATA_PROCESSED / "vor_parameters.csv", dtype={"value": str})
    relationships = pd.read_csv(config.HOQ_RELATIONSHIPS_CSV, index_col="item_id")
    roof = pd.read_csv(config.HOQ_ROOF_CSV)
    hoq = HouseOfQuality(vor, relationships, roof)

    ranking = hoq.ranking()
    ranking.to_csv(config.DATA_PROCESSED / "hoq_ranking.csv", index=False)
    selected = hoq.select_for_optimization(config.TOP_K_FOR_OPTIMIZATION)
    top_share = float(ranking.loc[ranking["ec"].isin(selected), "relative_importance_pct"].sum())

    table1 = ranking[
        ["engineering_characteristic", "vor_parameters_strong", "relationship_sum", "aic", "relative_importance_pct", "priority_rank"]
    ].rename(
        columns={
            "engineering_characteristic": "Engineering characteristic",
            "vor_parameters_strong": "VoR parameters (strong relationship)",
            "relationship_sum": "Relationship sum",
            "aic": "Wr-weighted AIC",
            "relative_importance_pct": "Share of total AIC (%)",
            "priority_rank": "Priority rank",
        }
    )
    write_table(table1, config.RESULTS_TABLES / "table1_hoq_aic_rankings", "Table 1 - House of Quality: AIC rankings (demonstration dataset)")

    conflicts = hoq.conflicts().assign(
        ec_a=lambda d: d["ec_a"].map(config.EC_LABELS), ec_b=lambda d: d["ec_b"].map(config.EC_LABELS)
    )
    write_table(conflicts, config.RESULTS_TABLES / "hoq_roof_conflicts", "HoQ roof: conflicting characteristic pairs (demonstration dataset)", "{:.0f}")
    write_json(
        {"selected_for_optimization": selected, "top_k": config.TOP_K_FOR_OPTIMIZATION, "selected_share_of_total_aic_pct": top_share},
        config.DATA_PROCESSED / "phase2_summary.json",
    )

    print("Table 1 - House of Quality: AIC rankings (this run's demonstration-dataset output)")
    for _, r in ranking.iterrows():
        print(f"  {int(r['priority_rank'])}. {r['engineering_characteristic']:<34} relationship sum {int(r['relationship_sum']):>3}"
              f"   AIC {r['aic']:6.2f}   ({r['relative_importance_pct']:.1f}% of total)")
    print(f"Selected for Taguchi optimization (top {config.TOP_K_FOR_OPTIMIZATION}): {', '.join(config.EC_LABELS[e] for e in selected)}"
          f" - {top_share:.1f}% of total AIC")
    print(f"Roof conflicts: {len(conflicts)}")


if __name__ == "__main__":
    main()
