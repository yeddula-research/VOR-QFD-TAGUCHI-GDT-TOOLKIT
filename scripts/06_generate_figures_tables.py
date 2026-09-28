"""Step 6 - figures from the demonstration dataset."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from vor_gdt import config, figures  # noqa: E402
from vor_gdt.reporting import read_json  # noqa: E402
from vor_gdt.robust_design import analyze_experiment  # noqa: E402


def main() -> None:
    config.RESULTS_FIGURES.mkdir(parents=True, exist_ok=True)
    selected = read_json(config.DATA_PROCESSED / "phase2_summary.json")["selected_for_optimization"]
    ranking = pd.read_csv(config.DATA_PROCESSED / "hoq_ranking.csv")
    res = analyze_experiment(pd.read_csv(config.TAGUCHI_MEASUREMENTS_CSV), selected)
    labels = dict(config.EC_LABELS)

    outputs = {
        "figure2_sn_ratio_trends.png": lambda p: figures.sn_trends(res["sn"], labels, p),
        "figure3_anova_contributions.png": lambda p: figures.anova_contributions(res["anova"], labels, p),
        "figure5_weighted_aic_scores.png": lambda p: figures.aic_ranking(ranking, selected, p),
        "main_effects_sn.png": lambda p: figures.main_effects_plot(res["main_effects"], labels, p),
    }
    for name, draw in outputs.items():
        draw(config.RESULTS_FIGURES / name)
        print(f"Wrote {(config.RESULTS_FIGURES / name).relative_to(config.REPO_ROOT)}")


if __name__ == "__main__":
    main()
