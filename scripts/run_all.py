"""Run the full pipeline: dataset -> VoR -> HoQ -> Taguchi -> GD&T -> figures -> published values."""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = [
    "01_generate_dataset.py",
    "02_extract_vor.py",
    "03_build_house_of_quality.py",
    "04_run_taguchi.py",
    "05_formulate_gdt_scheme.py",
    "06_generate_figures_tables.py",
    "07_published_values.py",
]


def main() -> None:
    for step in STEPS:
        print(f"\n=== {step} ===", flush=True)
        subprocess.run([sys.executable, str(HERE / step)], check=True)
    print("\nDone. Tables in results/tables/, figures in results/figures/.")


if __name__ == "__main__":
    main()
