#!/usr/bin/env python3
"""Check benchmark checksums, trial identities, graph pairing and aggregates."""

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from flpa.algorithms import PYTHON_ALGORITHMS
from flpa.experiments import RAW_COLUMNS, paired_summary, run_id, summarize


def verify(directory: Path) -> dict:
    """Recompute summaries from the raw CSV and validate the manifest plan."""
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["sha256"].items():
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest, name

    plan = manifest["plan"]
    raw = pd.read_csv(directory / "raw.csv")
    assert tuple(raw.columns) == RAW_COLUMNS, "unexpected CSV schema"
    expected = {
        run_id(plan, case, algorithm, graph, seed)
        for case in plan["cases"] for graph, seed in plan["seed_pairs"] for algorithm in plan["algorithms"]
    }
    assert len(raw) == len(expected) and set(raw.run_id) == expected, "missing or duplicate trials"
    assert raw.groupby(["case_id", "graph_seed"]).graph_sha256.nunique().eq(1).all(), "unpaired graphs"
    assert raw.graph_sha256.str.fullmatch(r"[0-9a-f]{64}").all(), "invalid graph hashes"

    successful = raw[raw.status == "ok"]
    failed = raw[raw.status != "ok"]
    supervised = successful[successful.n_communities_true.notna()]
    assert successful.runtime_seconds.gt(0).all(), "invalid measured runtime"
    assert successful.n_predicted_clusters.between(1, successful.n_nodes).all(), "invalid cluster counts"
    assert successful[successful.algorithm.isin(PYTHON_ALGORITHMS)].final_maximality.eq(True).all(), "maximality"
    assert failed[["acc", "nmi", "ari", "modularity", "n_predicted_clusters"]].isna().all().all(), "failed run scored"
    assert supervised.acc.between(0, 1).all(), "ACC out of range or missing"
    assert supervised.nmi.between(0, 1).all(), "NMI out of range or missing"
    assert supervised.ari.between(-1, 1).all(), "ARI out of range or missing"
    assert successful[successful.n_communities_true.isna()][["acc", "nmi", "ari"]].isna().all().all()
    assert raw.status.value_counts().to_dict() == manifest["counts"], "count mismatch"
    for filename, calculated in [("summary.csv", summarize(raw)), ("paired.csv", paired_summary(raw))]:
        saved = pd.read_csv(directory / filename)
        pd.testing.assert_frame_equal(saved, calculated, check_dtype=False, check_exact=False)
    return manifest["counts"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", type=Path, nargs="+")
    args = parser.parse_args()
    for directory in args.directories:
        print(f"{directory}: {verify(directory)}")


if __name__ == "__main__":
    main()
