"""Gap A: family framing x period and x loan-size terms in the saved August run.

Zero compute: parses the committed `association_summary.txt` (2026-08-31 run)
for the family-framing interaction coefficients and their HC3 and
country-clustered p-values. An interaction compares a level with the
reference level (pre-pandemic; small loans); it is not a within-group slope.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SOURCE = Path("reports/generated_full_dataset/association_summary.txt")
TERM = re.compile(r"family_mentions_per_100_words(?::C\((analysis_period|loan_size_band)\)\[T\.(\w+)\])?")
COEF = re.compile(r"^\s+- (\S+): coefficient (-?[\d.]+) \(95% CI \[(-?[\d.]+), (-?[\d.]+)\], p=([\d.]+)\)")
SENS = re.compile(r"^\s+- (\S+): HC3 p=([\d.]+) .*?clustered p=([\d.]+)")


def parse(text: str) -> dict:
    out = {"duration": {}, "binary": {}}
    coef_model, sens_seen = None, 0
    for line in text.splitlines():
        if "associated with funding speed" in line:
            coef_model = "duration"
        elif "log-odds of funding within 24 hours" in line:
            coef_model = "binary"
        if line.startswith("Cluster-Robust Sensitivity Check"):
            coef_model = None
        m = COEF.match(line)
        if m and coef_model and TERM.fullmatch(m.group(1)):
            out[coef_model].setdefault(m.group(1), {}).update(
                coefficient=float(m.group(2)), ci95_hc3=[float(m.group(3)), float(m.group(4))])
        m = SENS.match(line)
        if m and TERM.fullmatch(m.group(1)):
            # Sensitivity lists duration first, then the 24-hour model.
            model = "duration" if m.group(1) not in out["duration"] or \
                "clustered_p" not in out["duration"][m.group(1)] else "binary"
            out[model].setdefault(m.group(1), {}).update(
                hc3_p=float(m.group(2)), clustered_p=float(m.group(3)))
    return out


def main() -> int:
    result = parse(SOURCE.read_text())
    result["source"] = str(SOURCE)
    result["note"] = ("Interactions vs reference levels (pre-pandemic; small). Duration is "
                      "log(1 + days), negative = faster; binary is log-odds of 24-hour funding, "
                      "positive = faster. 48 country clusters, normal reference.")
    out = Path("reports/subgroup_inference/primary_family_interactions.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1))
    for model in ("duration", "binary"):
        for term, v in result[model].items():
            print(model, term, v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
