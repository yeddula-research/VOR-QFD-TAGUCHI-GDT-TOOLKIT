"""Step 5 - Phase 4: GD&T scheme formulation (ASME Y14.5-2018) and traceability mapping."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from vor_gdt import config  # noqa: E402
from vor_gdt.gdt import formulate_scheme  # noqa: E402
from vor_gdt.reporting import read_json, write_json, write_table  # noqa: E402
from vor_gdt.traceability import build_traceability_matrix, coverage  # noqa: E402


def main() -> None:
    ranking = pd.read_csv(config.DATA_PROCESSED / "hoq_ranking.csv")
    vor = pd.read_csv(config.DATA_PROCESSED / "vor_parameters.csv", dtype={"value": str})
    relationships = pd.read_csv(config.HOQ_RELATIONSHIPS_CSV, index_col="item_id")
    taguchi = read_json(config.DATA_PROCESSED / "taguchi_results.json")

    scheme = formulate_scheme(ranking, taguchi["optimal_tolerance_mm"])
    write_table(
        scheme.drop(columns=["ec"]).rename(
            columns={
                "priority_rank": "Priority rank",
                "engineering_characteristic": "Engineering characteristic",
                "aic": "AIC",
                "control": "Control",
                "category": "Category",
                "datums": "Datums",
                "tolerance_source": "Tolerance source",
                "callout": "Callout",
            }
        ),
        config.RESULTS_TABLES / "gdt_scheme",
        "GD&T scheme per ASME Y14.5-2018 (demonstration dataset)",
    )
    trace = build_traceability_matrix(scheme, vor, relationships)
    write_table(
        trace.drop(columns=["ec"]),
        config.RESULTS_TABLES / "traceability_matrix",
        "Traceability: GD&T callout <-> HoQ <-> VoR <-> P&ID (demonstration dataset)",
    )
    cov = coverage(trace, scheme, vor)
    write_json(cov, config.RESULTS_TABLES / "traceability_coverage.json")

    print("GD&T scheme (this run's demonstration-dataset output)")
    for _, r in scheme.iterrows():
        print(f"  {int(r['priority_rank'])}. {r['engineering_characteristic']:<34} {r['callout']:<24} [{r['tolerance_source']}]")
    print("Datums: " + "; ".join(f"{k} = {v}" for k, v in config.DATUMS.items()))
    print(f"Traceability links (R_ij >= {config.TRACE_RELATIONSHIP_THRESHOLD}): {len(trace)}")
    print(f"VoR parameters traced to a callout: {cov['vor_parameters_traced']}/{cov['vor_parameters']} ({cov['vor_coverage_pct']:.0f}%)")
    print(f"Callouts traced to a VoR parameter: {cov['callouts_traced']}/{cov['callouts']} ({cov['callout_coverage_pct']:.0f}%)")


if __name__ == "__main__":
    main()
