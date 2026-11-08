"""Gap E: split the November linear text gain into form, lexicon and TF-IDF.

Zero compute: reads the reviewed benchmark's saved MAE for the nested linear
arms S, S+M, S+M+L, S+M+L+R and text-only T. Stage gains are differences of
total gains against S on identical rows; they depend on the nesting order.
"""
from __future__ import annotations

import json
from pathlib import Path

SOURCE = Path("reports/text_benchmark_reviewed/benchmark.json")


def main() -> int:
    bench = json.loads(SOURCE.read_text())
    mae = {(m["year"], m["arm"]): m["metrics"]["mae_days"]
           for m in bench["models"] if m["family"] == "linear"}
    rows = []
    for year in sorted({y for y, _ in mae}):
        s = mae[year, "S"]
        rows.append({"year": year, "mae_S": s,
                     "form_M": s - mae[year, "S+M"],
                     "lexicon_L_after_M": mae[year, "S+M"] - mae[year, "S+M+L"],
                     "tfidf_R_after_ML": mae[year, "S+M+L"] - mae[year, "S+M+L+R"],
                     "total": s - mae[year, "S+M+L+R"],
                     "text_only_T_minus_S": s - mae[year, "T"]})
    out = Path("reports/gain_breakdown/gain_breakdown.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"source": str(SOURCE), "unit": "days of MAE, positive = better",
                               "rows": rows}, indent=1))
    for r in rows:
        print({k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
