"""Table writers (CSV / Markdown / JSON) used by the pipeline scripts."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def to_markdown(df: pd.DataFrame, floatfmt: str = "{:.2f}") -> str:
    """Render ``df`` as a GitHub-flavoured Markdown table (no extra dependencies)."""

    def fmt(v):
        if isinstance(v, (float, np.floating)):
            return "" if np.isnan(v) else floatfmt.format(v)
        return str(v).replace("|", "\\|")

    header = "| " + " | ".join(fmt(c) for c in df.columns) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    body = ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([header, sep, *body]) + "\n"


def write_table(df: pd.DataFrame, stem: Path, title: str | None = None, floatfmt: str = "{:.2f}") -> None:
    """Write ``df`` to ``<stem>.csv`` and ``<stem>.md``."""
    stem.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(stem.with_suffix(".csv"), index=False)
    md = to_markdown(df, floatfmt)
    if title:
        md = f"**{title}**\n\n{md}"
    stem.with_suffix(".md").write_text(md, encoding="utf-8")


def write_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=float) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
