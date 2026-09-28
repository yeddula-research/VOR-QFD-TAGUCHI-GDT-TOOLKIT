"""Figures written by ``scripts/06_generate_figures_tables.py``.

Series colours are the first three slots of a colour-vision-deficiency
validated categorical palette; every multi-series chart also varies line
style and marker so identity never depends on colour alone.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"
NEUTRAL = "#a9a8a2"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
LINESTYLES = ["-", "--", ":"]
MARKERS = ["o", "s", "^"]


def _style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(NEUTRAL)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _figure(width: float, height: float, ncols: int = 1):
    fig, axes = plt.subplots(1, ncols, figsize=(width, height), facecolor=SURFACE)
    return fig, np.atleast_1d(axes)


def sn_trends(sn: pd.DataFrame, labels: Mapping[str, str], path: Path) -> None:
    """S/N ratio of each characteristic across the inner-array runs."""
    fig, (ax,) = _figure(8.0, 4.2)
    _style(ax)
    runs = list(sn.index)
    for i, ec in enumerate(sn.columns):
        ax.plot(
            runs, sn[ec], color=SERIES[i], linestyle=LINESTYLES[i], marker=MARKERS[i],
            linewidth=2, markersize=8, markeredgecolor=SURFACE, markeredgewidth=1.5, label=labels[ec],
        )
        ax.annotate(
            labels[ec], (runs[-1], sn[ec].iloc[-1]), xytext=(8, 0), textcoords="offset points",
            va="center", fontsize=8.5, color=TEXT_PRIMARY,
        )
    ax.set_xticks(runs)
    ax.set_xticklabels([f"Run {r}" for r in runs])
    ax.set_xlim(runs[0] - 0.4, runs[-1] + 2.8)
    ax.set_ylabel("S/N ratio (dB)", color=TEXT_SECONDARY)
    ax.set_title("S/N ratio across the inner-array runs (demonstration dataset)", color=TEXT_PRIMARY, fontsize=11, loc="left")
    ax.legend(loc="upper center", bbox_to_anchor=(0.4, -0.12), ncol=3, frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def anova_contributions(anovas: Mapping[str, pd.DataFrame], labels: Mapping[str, str], path: Path) -> None:
    """Percentage contribution of each factor (and error) to each characteristic's S/N."""
    ecs = list(anovas)
    fig, axes = _figure(4.0 * len(ecs), 3.6, ncols=len(ecs))
    sources = ecs + ["Error"]
    colors = {ec: SERIES[i] for i, ec in enumerate(ecs)}
    colors["Error"] = NEUTRAL
    names = {**{ec: labels[ec].replace(" tolerance", "") + " tol." for ec in ecs}, "Error": "Error"}
    for ax, ec in zip(axes, ecs):
        _style(ax)
        ax.grid(True, axis="x", color=GRID)
        ax.grid(False, axis="y")
        tab = anovas[ec].set_index("source").loc[sources, "contribution_pct"]
        y = np.arange(len(sources))[::-1]
        ax.barh(y, tab.to_numpy(), color=[colors[s] for s in sources], height=0.62, edgecolor=SURFACE, linewidth=2)
        for yi, v in zip(y, tab.to_numpy()):
            ax.text(v + 1.5, yi, f"{v:.1f}%", va="center", fontsize=8.5, color=TEXT_PRIMARY)
        ax.set_yticks(y)
        ax.set_yticklabels([names[s] for s in sources], fontsize=8.5)
        ax.set_xlim(0, 115)
        ax.set_xlabel("Contribution to S/N variation (%)", color=TEXT_SECONDARY, fontsize=9)
        ax.set_title(f"S/N of: {labels[ec]}", color=TEXT_PRIMARY, fontsize=10, loc="left")
    fig.suptitle("ANOVA factor contributions (demonstration dataset)", x=0.01, ha="left", color=TEXT_PRIMARY, fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def aic_ranking(ranking: pd.DataFrame, selected: Sequence[str], path: Path) -> None:
    """Weighted AIC of each engineering characteristic, highest first."""
    fig, (ax,) = _figure(7.5, 3.6)
    _style(ax)
    ax.grid(True, axis="x", color=GRID)
    ax.grid(False, axis="y")
    y = np.arange(len(ranking))[::-1]
    sel = set(selected)
    colors = [SERIES[0] if ec in sel else NEUTRAL for ec in ranking["ec"]]
    ax.barh(y, ranking["aic"], color=colors, height=0.62, edgecolor=SURFACE, linewidth=2)
    xmax = float(ranking["aic"].max())
    for yi, v, share in zip(y, ranking["aic"], ranking["relative_importance_pct"]):
        ax.text(v + xmax * 0.015, yi, f"{v:.1f}  ({share:.1f}%)", va="center", fontsize=8.5, color=TEXT_PRIMARY)
    ax.set_yticks(y)
    ax.set_yticklabels(ranking["engineering_characteristic"], fontsize=9)
    ax.set_xlim(0, xmax * 1.3)
    ax.set_xlabel("Weighted AIC (Eq. 2)", color=TEXT_SECONDARY)
    fig.suptitle(
        "House of Quality: weighted AIC by characteristic (demonstration dataset)",
        x=0.01, ha="left", color=TEXT_PRIMARY, fontsize=11,
    )
    from matplotlib.patches import Patch

    ax.legend(
        handles=[Patch(color=SERIES[0], label="Selected for Taguchi optimization"), Patch(color=NEUTRAL, label="Specified, not optimized")],
        loc="lower right", frameon=False, fontsize=8.5,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def published_sn_trends(table2_runs: pd.DataFrame, responses: Mapping[str, str], path: Path) -> None:
    """Figure 2 of the paper, plotted from the S/N values in its Table 2."""
    fig, (ax,) = _figure(8.0, 4.2)
    _style(ax)
    runs = np.arange(1, len(table2_runs) + 1)
    for i, (label, col) in enumerate(responses.items()):
        ax.plot(
            runs, table2_runs[col], color=SERIES[i], linestyle=LINESTYLES[i], marker=MARKERS[i],
            linewidth=2, markersize=8, markeredgecolor=SURFACE, markeredgewidth=1.5, label=label,
        )
    ax.set_xticks(runs)
    ax.set_xticklabels([f"Run {r}" for r in runs])
    ax.set_ylim(10, 21)
    ax.set_ylabel("S/N ratio (dB)", color=TEXT_SECONDARY)
    ax.set_title("Figure 2: S/N ratio trends across the nine Taguchi runs (data: Table 2)", color=TEXT_PRIMARY, fontsize=11, loc="left")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def published_aic_radar(labels: Sequence[str], values: Sequence[float], path: Path) -> None:
    """Figure 5 of the paper (radar chart), plotted from the AIC values in its Table 1."""
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    closed_angles = np.concatenate([angles, angles[:1]])
    closed_values = np.concatenate([np.asarray(values, dtype=float), [values[0]]])
    fig = plt.figure(figsize=(8.4, 7.0), facecolor=SURFACE)
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor(SURFACE)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.plot(closed_angles, closed_values, color=SERIES[0], linewidth=2, marker="o", markersize=8,
            markeredgecolor=SURFACE, markeredgewidth=1.5)
    ax.fill(closed_angles, closed_values, color=SERIES[0], alpha=0.12)
    for a, v in zip(angles, values):
        ax.annotate(f"{v:.1f}", (a, v), xytext=(0, -18), textcoords="offset points", ha="center", fontsize=8.5, color=TEXT_PRIMARY)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=8.5, color=TEXT_SECONDARY)
    ax.tick_params(axis="x", pad=16)
    ax.set_rlabel_position(330)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=8, color=TEXT_SECONDARY)
    ax.grid(color=GRID)
    ax.spines["polar"].set_color(NEUTRAL)
    ax.set_title("Figure 5: weighted AIC scores from the HoQ matrix (data: Table 1)",
                 color=TEXT_PRIMARY, fontsize=10.5, pad=40)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def main_effects_plot(effects: Mapping[str, pd.DataFrame], labels: Mapping[str, str], path: Path) -> None:
    """Main-effects plot: mean S/N per level of every factor, one panel per characteristic."""
    ecs = list(effects)
    fig, axes = _figure(4.0 * len(ecs), 3.6, ncols=len(ecs))
    for ax, ec in zip(axes, ecs):
        _style(ax)
        me = effects[ec]
        for i, factor in enumerate(me.columns):
            ax.plot(
                np.arange(1, len(me) + 1), me[factor], color=SERIES[i], linestyle=LINESTYLES[i], marker=MARKERS[i],
                linewidth=2, markersize=8, markeredgecolor=SURFACE, markeredgewidth=1.5,
                label=labels[factor].replace(" tolerance", "") + " tol.",
            )
        ax.set_xticks(np.arange(1, len(me) + 1))
        ax.set_xticklabels([f"L{k}" for k in range(1, len(me) + 1)])
        ax.set_xlabel("Factor level (1 = tightest)", color=TEXT_SECONDARY, fontsize=9)
        ax.set_ylabel("Mean S/N (dB)", color=TEXT_SECONDARY, fontsize=9)
        ax.set_title(f"S/N of: {labels[ec]}", color=TEXT_PRIMARY, fontsize=10, loc="left")
    axes[0].legend(frameon=False, fontsize=8, loc="lower left")
    fig.suptitle("Main effects of the control factors (demonstration dataset)", x=0.01, ha="left", color=TEXT_PRIMARY, fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)
