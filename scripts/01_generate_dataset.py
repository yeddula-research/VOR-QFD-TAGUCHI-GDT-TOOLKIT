"""Step 1 - generate the simulated demonstration dataset into data/raw/."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vor_gdt import config  # noqa: E402
from vor_gdt.data_generation import write_dataset  # noqa: E402


def main() -> None:
    ds = write_dataset(config.RANDOM_SEED)
    m = ds["measurements"]
    print(config.DATASET_DISCLOSURE)
    print(f"P&ID register items:           {len(ds['register'])}  -> {config.PID_REGISTER_CSV.relative_to(config.REPO_ROOT)}")
    print(f"HoQ relationship matrix:       {ds['relationships'].shape[0]} x {ds['relationships'].shape[1]}  -> "
          f"{config.HOQ_RELATIONSHIPS_CSV.relative_to(config.REPO_ROOT)}")
    print(f"Characteristics to optimize:   {', '.join(ds['selected'])}")
    print(f"Inner array: {ds['inner_array']}, outer array: {config.OUTER_ARRAY} "
          f"({len(config.NOISE_FACTORS)} noise factors), replicates: {config.REPLICATES_PER_NOISE_CONDITION}")
    print(f"Taguchi measurements:          {len(m)} rows  -> {config.TAGUCHI_MEASUREMENTS_CSV.relative_to(config.REPO_ROOT)}")
    print(f"Random seed:                   {config.RANDOM_SEED}")


if __name__ == "__main__":
    main()
