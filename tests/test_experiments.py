from pathlib import Path

import pandas as pd
import pytest

from flpa import Graph
from flpa.experiments import RAW_COLUMNS, iter_runs, load_plan, paired_summary, run_trial, summarize


CONFIG = Path(__file__).resolve().parents[1] / "configs" / "e3_ablation.json"


def test_run_schema_pairing_and_sample_sd():
    plan = load_plan(CONFIG, "smoke")
    rows = list(iter_runs(plan))
    assert all(tuple(row) == RAW_COLUMNS for row in rows)
    assert {row["status"] for row in rows} == {"ok"}
    assert len({row["graph_sha256"] for row in rows}) == 1
    assert len({row["algorithm_seed"] for row in rows}) == 1
    assert {row["graph_seed"] for row in rows}.isdisjoint(row["algorithm_seed"] for row in rows)
    summary = summarize(pd.DataFrame(rows))
    assert summary.n_ok.eq(1).all()
    assert summary.runtime_seconds_sd.isna().all()
    assert summary.n_final_maximal.eq(1).all()
    assert paired_summary(pd.DataFrame(rows)).n_paired_ok.eq(1).all()


def test_timeout_and_failure_appear_in_summary(monkeypatch):
    real = run_trial

    def capped(graph, truth, algorithm, seed, timeout):
        if algorithm == "flpa_lifo":
            return real(graph, truth, algorithm, seed, 1e-12)
        if algorithm == "flpa_all":
            return real(graph, truth, "unavailable", seed, timeout)
        return real(graph, truth, algorithm, seed, timeout)

    monkeypatch.setattr("flpa.experiments.run_trial", capped)
    raw = pd.DataFrame(iter_runs(load_plan(CONFIG, "smoke")))
    assert raw.status.tolist() == ["ok", "timeout", "error"]
    assert raw[raw.status != "ok"].nmi.isna().all()
    summary = summarize(raw).set_index("algorithm")
    assert summary.loc["flpa_lifo", "n_timeout"] == 1
    assert summary.loc["flpa_all", "n_other_failure"] == 1
    assert summary.loc["flpa_all", "completion_rate"] == 0
    assert paired_summary(raw).n_paired_ok.eq(0).all()


def test_paired_ratio_is_distinct_from_ratio_of_means():
    plan = load_plan(CONFIG, "smoke")
    rows = list(iter_runs(plan))
    fifo, lifo, _ = rows
    first = [{**fifo, "runtime_seconds": 1}, {**lifo, "runtime_seconds": 2}]
    second = [{**fifo, "runtime_seconds": 3, "algorithm_seed": 1},
              {**lifo, "runtime_seconds": 3, "algorithm_seed": 1}]
    row = paired_summary(pd.DataFrame(first + second)).iloc[0]
    assert row.speedup_mean == pytest.approx(1.5)
    assert row.ratio_of_paired_means == pytest.approx(1.25)


def test_native_leiden_timeout_is_reported():
    graph = Graph.from_edges([10, 80], [(10, 80)])
    row = run_trial(graph, None, "leiden", 42, 1e-12)
    assert row["status"] == "timeout"
    assert "n_predicted_clusters" not in row
