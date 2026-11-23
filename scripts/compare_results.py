#!/usr/bin/env python3
"""Compare E1 with digitized Figure 1 and the paired author implementation."""

import argparse
from pathlib import Path

import pandas as pd


def compare(python_results: Path, author_results: Path, paper_values: Path, output: Path) -> None:
    """Write an approximate paper comparison and measured same-graph backend comparison."""
    output.mkdir(parents=True, exist_ok=True)
    python_summary = pd.read_csv(python_results / "summary.csv")
    keys = ["dataset", "n_nodes", "algorithm"]
    aggregate = python_summary[keys + ["n_ok", "runtime_seconds_mean", "runtime_seconds_sd"]]
    digitized = pd.read_csv(paper_values).merge(aggregate, on=keys, validate="one_to_one")
    digitized["relative_deviation_pct"] = 100 * (
        digitized.runtime_seconds_mean / digitized.mean_seconds_approx - 1
    )
    digitized.to_csv(output / "e1_figure1.csv", index=False)

    reference = pd.read_csv(author_results / "raw.csv")
    ours = pd.read_csv(python_results / "raw.csv")
    pairing = keys + ["case_id", "graph_seed", "algorithm_seed", "graph_sha256"]
    paired = reference.merge(ours, on=pairing, suffixes=("_author", "_python"), validate="one_to_one")
    if len(paired) != len(reference):
        raise ValueError("author trials do not match Python topology and seed")
    rows = []
    for group_key, group in paired.groupby(keys, sort=True):
        completed = group[(group.status_python == "ok") & (group.status_author == "ok")]
        row = dict(zip(keys, group_key))
        row.update(n_pairs=len(group), n_paired_ok=len(completed))
        for metric in ("runtime_seconds", "n_predicted_clusters", "nmi", "ari", "acc"):
            author = completed[f"{metric}_author"]
            python = completed[f"{metric}_python"]
            row[f"{metric}_author_mean"] = author.mean()
            row[f"{metric}_python_mean"] = python.mean()
            row[f"{metric}_author_sd"] = author.std(ddof=1)
            row[f"{metric}_python_sd"] = python.std(ddof=1)
            row[f"{metric}_delta_mean"] = (python - author).mean()
        row["runtime_relative_deviation_pct"] = 100 * (
            row["runtime_seconds_python_mean"] / row["runtime_seconds_author_mean"] - 1
        )
        rows.append(row)
    pd.DataFrame(rows).to_csv(output / "e1_author_same_graph.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, default=Path("results/e1"))
    parser.add_argument("--reference", type=Path, default=Path("results/author/e1"))
    parser.add_argument("--paper", type=Path, default=Path("data/figure1_reference.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/comparison"))
    args = parser.parse_args()
    compare(args.python, args.reference, args.paper, args.output)
