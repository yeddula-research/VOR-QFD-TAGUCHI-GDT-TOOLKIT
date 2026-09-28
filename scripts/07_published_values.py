"""Step 7 - the paper's results: Tables 1-3, Figures 2 and 5, consistency checks.

Nothing here is computed from the demonstration dataset. The tables are copied
from the paper; Figures 2 and 5 are plotted from those tables; and the
main-effects check derives the optimal tolerance setting from the paper's own
Table 2 values.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vor_gdt import config, figures, published  # noqa: E402
from vor_gdt.reporting import write_table  # noqa: E402

NOTE = "source: the paper"


def main() -> None:
    config.RESULTS_TABLES.mkdir(parents=True, exist_ok=True)
    config.RESULTS_FIGURES.mkdir(parents=True, exist_ok=True)

    write_table(
        published.TABLE1,
        config.RESULTS_TABLES / "table1_hoq_aic_rankings_as_reported",
        f"Table 1 - House of Quality: AIC rankings of engineering characteristics ({NOTE})",
        "{:.1f}",
    )
    write_table(
        published.table2_as_printed(),
        config.RESULTS_TABLES / "table2_taguchi_l9_sn_ratios_as_reported",
        f"Table 2 - Taguchi L9 orthogonal array: S/N ratio results for top three characteristics ({NOTE})",
    )
    write_table(
        published.TABLE3,
        config.RESULTS_TABLES / "table3_benchmarking_as_reported",
        f"Table 3 - Quantitative benchmarking against conventional design methods ({NOTE})",
    )
    write_table(
        published.table2_main_effects(),
        config.RESULTS_TABLES / "table2_main_effects_as_reported",
        "Main effects computed from the S/N values published in the paper's Table 2",
        "{:.3f}",
    )

    runs = published.table2_runs()
    figures.published_sn_trends(
        runs,
        {
            "Wall thickness tolerance": published.TABLE2_RESPONSES["Wall thickness tolerance"],
            "Bore positional tolerance": published.TABLE2_RESPONSES["Bore position tolerance"],
            "Flange face flatness": published.TABLE2_RESPONSES["Flange flatness"],
        },
        config.RESULTS_FIGURES / "figure2_sn_ratio_trends_as_reported.png",
    )
    figures.published_aic_radar(
        list(published.TABLE1["Engineering characteristic"]),
        list(published.TABLE1["Wr-weighted AIC"]),
        config.RESULTS_FIGURES / "figure5_weighted_aic_radar_as_reported.png",
    )

    derived = published.table2_optimum()
    reported = published.table2_reported_optimum()
    print(f"Published values ({published.SOURCE})")
    print("  Tables 1-3 written to results/tables/*_as_reported.*")
    print("  Figures 2 and 5 plotted from Tables 2 and 1 -> results/figures/*_as_reported.png")
    print(f"  Table 2 design is the standard L9 array (columns 1-3): {published.table2_is_l9()}")
    print(f"  Table 1 priority ranks follow its AIC order: {published.table1_ranks_follow_aic()}")
    print("  Optimum from main effects of the published Table 2 S/N values:")
    for factor, tol in derived.items():
        print(f"    {factor:<26} {tol:g} mm  (Table 2 'Optimal' row: {reported[factor]:g} mm)")
    print(f"  Matches the paper's reported optimum: {derived == reported}")


if __name__ == "__main__":
    main()
