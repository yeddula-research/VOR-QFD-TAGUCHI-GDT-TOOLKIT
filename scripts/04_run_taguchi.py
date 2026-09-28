"""Step 4 - Phase 3: Taguchi robust design (Eq. 3), ANOVA, confirmation -> Table 2."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from vor_gdt import config  # noqa: E402
from vor_gdt.data_generation import simulate_confirmation  # noqa: E402
from vor_gdt.reporting import read_json, write_json, write_table  # noqa: E402
from vor_gdt.robust_design import analyze_experiment, confirmation_sn, format_level  # noqa: E402

SHORT = {
    "shell_wall_thickness": "wall",
    "nozzle_bore_position": "bore",
    "flange_face_flatness": "flatness",
}


def main() -> None:
    selected = read_json(config.DATA_PROCESSED / "phase2_summary.json")["selected_for_optimization"]
    measurements = pd.read_csv(config.TAGUCHI_MEASUREMENTS_CSV)
    res = analyze_experiment(measurements, selected)
    design, sn = res["design"], res["sn"]
    sn.to_csv(config.DATA_PROCESSED / "taguchi_sn_by_run.csv")

    # Confirmation experiment at the optimum (fresh seed).
    confirm = simulate_confirmation(selected, res["optimum_levels"])
    confirm.to_csv(config.CONFIRMATION_MEASUREMENTS_CSV, index=False, float_format="%.5f")
    observed = confirmation_sn(confirm, selected)

    # Table 2: runs, then optimum (predicted) and confirmation (observed).
    rows = []
    for run in design.index:
        row = {"Run": f"Run {run}"}
        for ec in selected:
            row[f"{config.CONTROL_FACTORS[ec]['factor']}"] = format_level(ec, int(design.loc[run, ec]))
        for ec in selected:
            row[f"S/N {SHORT.get(ec, ec)} (dB)"] = sn.loc[run, ec]
        rows.append(row)
    for label, values in (("Optimum - predicted", res["predicted_sn"]), ("Optimum - confirmation run", observed)):
        row = {"Run": label}
        for ec in selected:
            row[f"{config.CONTROL_FACTORS[ec]['factor']}"] = format_level(ec, res["optimum_levels"][ec])
        for ec in selected:
            row[f"S/N {SHORT.get(ec, ec)} (dB)"] = values[ec]
        rows.append(row)
    table2 = pd.DataFrame(rows)
    write_table(table2, config.RESULTS_TABLES / "table2_taguchi_l9_sn_ratios", "Table 2 - Taguchi inner array: S/N ratios (demonstration dataset)")

    # ANOVA and main effects.
    own_contribution = {}
    effects_rows = []
    for ec in selected:
        a = res["anova"][ec].copy()
        a["source"] = a["source"].map(lambda s: config.CONTROL_FACTORS[s]["factor"] if s in config.CONTROL_FACTORS else s)
        write_table(a, config.RESULTS_TABLES / f"anova_{ec}", f"ANOVA of S/N - {config.EC_LABELS[ec]} (demonstration dataset)", "{:.3f}")
        own_contribution[ec] = float(res["anova"][ec].set_index("source").loc[ec, "contribution_pct"])
        me = res["main_effects"][ec]
        for factor in me.columns:
            for level, value in me[factor].items():
                effects_rows.append(
                    {
                        "characteristic_sn": config.EC_LABELS[ec],
                        "factor": config.CONTROL_FACTORS[factor]["factor"],
                        "level": int(level) + 1,
                        "tolerance": format_level(factor, int(level)),
                        "mean_sn_db": value,
                    }
                )
    write_table(pd.DataFrame(effects_rows), config.RESULTS_TABLES / "main_effects_sn", "Main effects on S/N (demonstration dataset)", "{:.3f}")

    write_json(
        {
            "inner_array": "L9" if len(design) == 9 else "L18",
            "selected": selected,
            "sn_type": {ec: config.CONTROL_FACTORS[ec]["sn_type"] for ec in selected},
            "optimum_levels": res["optimum_levels"],
            "optimal_tolerance_mm": res["optimal_tolerance"],
            "predicted_sn_db": res["predicted_sn"],
            "confirmation_sn_db": observed,
            "best_single_run": res["best_run"],
            "own_factor_contribution_pct": own_contribution,
        },
        config.DATA_PROCESSED / "taguchi_results.json",
    )

    print(f"Table 2 - Taguchi {'L9' if len(design) == 9 else 'L18'} S/N ratios (this run's demonstration-dataset output)")
    header = "  Run      " + "".join(f"{SHORT.get(ec, ec):>11}" for ec in selected)
    print(header)
    for run in design.index:
        print(f"  Run {run:<5}" + "".join(f"{sn.loc[run, ec]:11.2f}" for ec in selected))
    print("  Optimum  " + "".join(f"{format_level(ec, res['optimum_levels'][ec]):>11}" for ec in selected))
    print("  Predicted" + "".join(f"{res['predicted_sn'][ec]:11.2f}" for ec in selected))
    print("  Confirm. " + "".join(f"{observed[ec]:11.2f}" for ec in selected))
    for ec in selected:
        print(f"ANOVA: {config.CONTROL_FACTORS[ec]['factor']} explains {own_contribution[ec]:.1f}% of the {config.EC_LABELS[ec]} S/N variation")


if __name__ == "__main__":
    main()
