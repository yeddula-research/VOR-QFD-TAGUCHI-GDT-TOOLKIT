"""Step 2 - Phase 1: extract Voice of Regulation parameters and weight them (Eq. 1)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from vor_gdt import config  # noqa: E402
from vor_gdt.reporting import write_json, write_table  # noqa: E402
from vor_gdt.vor import extract_vor, summarize_by_source, weight_vor  # noqa: E402


def main() -> None:
    register = pd.read_csv(config.PID_REGISTER_CSV, dtype={"value": str})
    vor, w_r = weight_vor(extract_vor(register))
    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    vor.to_csv(config.DATA_PROCESSED / "vor_parameters.csv", index=False)

    table = vor[["item_id", "pid_tag", "parameter", "source_name", "severity", "compliance_criticality", "weight"]].rename(
        columns={
            "item_id": "Item",
            "pid_tag": "P&ID tag",
            "parameter": "VoR parameter",
            "source_name": "Regulatory source",
            "severity": "S_i",
            "compliance_criticality": "C_i",
            "weight": "W_r,i",
        }
    )
    write_table(table, config.RESULTS_TABLES / "vor_parameters", "VoR parameters extracted from the P&ID register (demonstration dataset)", "{:.3f}")
    by_source = summarize_by_source(vor)
    write_table(by_source, config.RESULTS_TABLES / "vor_by_source", "VoR parameters by regulatory source (demonstration dataset)", "{:.3f}")
    write_json(
        {"register_items": len(register), "vor_parameters": len(vor), "aggregate_w_r": w_r},
        config.DATA_PROCESSED / "phase1_summary.json",
    )

    print(f"Register items: {len(register)}; VoR (CTQ) parameters extracted: {len(vor)}")
    print(f"Aggregate regulatory criticality weight W_r (Eq. 1): {w_r:.3f}")
    for _, r in by_source.iterrows():
        print(f"  {r['source_name']:<52} {int(r['parameters']):>2} parameters, sum W_r,i = {r['total_weight']:.3f}")


if __name__ == "__main__":
    main()
