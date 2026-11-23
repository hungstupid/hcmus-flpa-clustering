#!/usr/bin/env python3
"""Run a locked benchmark profile and persist evidence in a fresh directory."""

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd

from flpa.baselines import AUTHOR_COMMIT
from flpa.experiments import RAW_COLUMNS, environment, iter_runs, load_plan, paired_summary, summarize
from flpa.plotting import save_figures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--profile", choices=("smoke", "pilot", "main", "reference"), default="smoke")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--author-reference", type=Path, help="separate C reference binary for E1")
    args = parser.parse_args()

    plan = load_plan(args.config, args.profile)
    reference = args.author_reference.resolve() if args.author_reference else None
    if (args.profile == "reference") != bool(reference):
        parser.error("the reference profile requires --author-reference and vice versa")
    if reference is not None:
        actual = subprocess.check_output([str(reference), "--commit"], text=True, timeout=5).strip()
        if actual != AUTHOR_COMMIT:
            parser.error(f"expected the author reference at {AUTHOR_COMMIT}")
        plan["author_commit"] = actual
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"schema_version": 1, "plan": plan, "environment": environment(Path(__file__).resolve().parents[1])}
    total = len(plan["cases"]) * len(plan["seed_pairs"]) * len(plan["algorithms"])
    with (output / "raw.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=RAW_COLUMNS)
        writer.writeheader()
        for index, row in enumerate(iter_runs(plan, reference=reference), 1):
            writer.writerow(row)
            file.flush()
            if index % 12 == 0 or index == total or row["status"] != "ok":
                print(f"{index}/{total} {row['run_id']} {row['status']}", flush=True)

    raw = pd.read_csv(output / "raw.csv")
    summary = summarize(raw)
    summary.to_csv(output / "summary.csv", index=False)
    paired_summary(raw).to_csv(output / "paired.csv", index=False)
    save_figures(plan["experiment_type"], summary, output / "figures")
    manifest["counts"] = {key: int(value) for key, value in raw.status.value_counts().items()}
    manifest["sha256"] = {
        str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output.rglob("*")) if path.is_file()
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{output}: {manifest['counts']}", flush=True)


if __name__ == "__main__":
    main()
