"""Benchmark configurations, execution and paired summaries for E1 and E3."""

import json
import multiprocessing as mp
import os
import platform
import subprocess
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from typing import Iterator

import pandas as pd

from .algorithms import PYTHON_ALGORITHMS, DetectionResult, detect_communities, labels_are_maximal
from .baselines import run_author_reference, run_leiden, to_igraph
from .data import generate_graph, graph_statistics
from .metrics import evaluate_partition


RAW_COLUMNS = (
    "run_id", "experiment_id", "experiment_type", "profile", "case_id", "dataset",
    "algorithm", "order_position", "n_nodes", "n_edges", "n_isolates", "n_communities_true",
    "target_average_degree", "average_degree", "mixing_mu", "mixing_mu_realized",
    "graph_seed", "algorithm_seed", "graph_sha256", "graph_preparation_seconds",
    "timeout_seconds", "runtime_seconds", "nmi", "ari", "acc", "modularity",
    "n_predicted_clusters", "node_visits", "update_visits", "check_visits", "label_updates",
    "neighbor_examinations", "sweeps", "requeues", "final_maximality", "status", "backend", "error",
)
GROUP = ["case_id", "dataset", "n_nodes", "target_average_degree", "mixing_mu"]
MEASURES = [
    "runtime_seconds", "nmi", "ari", "acc", "modularity", "n_predicted_clusters",
    "node_visits", "update_visits", "check_visits", "label_updates", "neighbor_examinations", "requeues",
]


def load_plan(path: Path, profile: str) -> dict:
    """Expand a JSON configuration into cases and independent seed pairs."""
    config = json.loads(path.read_text(encoding="utf-8"))
    settings = config["profiles"][profile]
    cases = []
    for scenario in config["scenarios"]:
        name = scenario["dataset"]
        degree = scenario["average_degree"]
        mixing_values = scenario.get("mixing_values", [None])
        if name == "sbm":
            mixing_values = settings.get("mixing_values", mixing_values)
        for size in settings.get("sizes", scenario["sizes"]):
            for mu in mixing_values:
                case_id = f"{name}-{size}-d{degree:g}" + (f"-mu{mu:g}" if mu is not None else "")
                cases.append({
                    "case_id": case_id, "dataset": name, "n_nodes": size, "average_degree": degree,
                    "mixing_mu": mu, "n_communities": scenario.get("n_communities"),
                })
    algorithms = settings.get("algorithms", config["algorithms"])
    if not algorithms or set(algorithms).difference((*PYTHON_ALGORITHMS, "leiden")):
        raise ValueError("the configuration contains an unsupported algorithm")
    if len(set(algorithms)) != len(algorithms) or len({c["case_id"] for c in cases}) != len(cases):
        raise ValueError("duplicate algorithms or cases")
    seed_pairs = [
        [config["graph_seed_start"] + repeat, config["algorithm_seed_start"] + repeat]
        for repeat in range(settings["repeats"])
    ]
    if not cases or not seed_pairs or config["timeout_seconds"] <= 0:
        raise ValueError("the experiment must have cases, seeds and a positive timeout")
    return {
        "experiment_id": config["experiment_id"], "experiment_type": config["experiment_type"],
        "profile": profile, "algorithms": algorithms, "cases": cases, "seed_pairs": seed_pairs,
        "timeout_seconds": config["timeout_seconds"],
    }


def run_id(plan: dict, case: dict, algorithm: str, graph_seed: int, algorithm_seed: int) -> str:
    """Use a stable trial name across CSV, tracking and verification."""
    return f"{plan['experiment_id']}-{plan['profile']}-{case['case_id']}-{algorithm}-g{graph_seed}-a{algorithm_seed}"


def _leiden_worker(graph, seed, pipe):
    with pipe:
        try:
            prepared = to_igraph(graph)
            pipe.send(("ready", None))
            pipe.send(("result", run_leiden(prepared, seed)))
        except Exception as exc:
            pipe.send(("error", f"{type(exc).__name__}: {exc}"))


def _run_leiden_with_timeout(graph, seed, timeout):
    context = mp.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_leiden_worker, args=(graph, seed, sender))
    with receiver, sender:
        process.start()
        sender.close()
        try:
            if not receiver.poll(60):
                raise RuntimeError("Leiden graph preparation exceeded 60 seconds")
            stage, payload = receiver.recv()
            if stage != "ready":
                raise RuntimeError(payload)
            start = perf_counter()
            if not receiver.poll(timeout):
                return DetectionResult((), perf_counter() - start, "timeout", "leidenalg+igraph")
            stage, payload = receiver.recv()
            if stage != "result":
                raise RuntimeError(payload)
            if payload.runtime_seconds >= timeout:
                return DetectionResult((), payload.runtime_seconds, "timeout", payload.backend)
            return payload
        finally:
            if process.is_alive():
                process.terminate()
            process.join(2)
            if process.is_alive():
                process.kill()
                process.join()
            process.close()


def run_trial(graph, truth, algorithm, algorithm_seed, timeout, *, reference=None) -> dict:
    """Run one algorithm and preserve status even when results cannot be scored."""
    try:
        if reference is not None:
            result = run_author_reference(reference, graph, algorithm, algorithm_seed, timeout)
        elif algorithm == "leiden":
            result = _run_leiden_with_timeout(graph, algorithm_seed, timeout)
        else:
            result = detect_communities(graph, algorithm, algorithm_seed, timeout=timeout)
        scores = {key: getattr(result, key) for key in (
            "runtime_seconds", "status", "backend", "node_visits", "update_visits", "check_visits",
            "label_updates", "neighbor_examinations", "sweeps", "requeues",
        )}
        if result.status != "ok":
            return scores
        if algorithm in PYTHON_ALGORITHMS:
            scores["final_maximality"] = labels_are_maximal(graph, result.labels)
            if not scores["final_maximality"]:
                scores.update(status="invariant_failed", error="final label is not maximal")
                return scores
        scores.update(evaluate_partition(graph, result.labels, truth))
        return scores
    except Exception as exc:
        backend = "leidenalg+igraph" if algorithm == "leiden" else "python"
        return {
            "status": "error", "backend": "igraph-author-reference" if reference else backend,
            "error": f"{type(exc).__name__}: {exc}",
        }


def iter_runs(plan: dict, *, reference=None) -> Iterator[dict]:
    """Yield trials sequentially, sharing a graph instance across algorithms."""
    algorithms = plan["algorithms"]
    timeout = plan["timeout_seconds"]
    for case in plan["cases"]:
        for repeat, (graph_seed, algorithm_seed) in enumerate(plan["seed_pairs"]):
            start = perf_counter()
            dataset = generate_graph(case, graph_seed)
            preparation = perf_counter() - start
            stats = graph_statistics(dataset)
            offset = repeat % len(algorithms)
            order = algorithms[offset:] + algorithms[:offset]
            for position, algorithm in enumerate(order):
                row = dict.fromkeys(RAW_COLUMNS)
                row.update({
                    "run_id": run_id(plan, case, algorithm, graph_seed, algorithm_seed),
                    "experiment_id": plan["experiment_id"], "experiment_type": plan["experiment_type"],
                    "profile": plan["profile"], "case_id": case["case_id"], "dataset": case["dataset"],
                    "algorithm": algorithm, "order_position": position, "graph_seed": graph_seed,
                    "algorithm_seed": algorithm_seed, "target_average_degree": case["average_degree"],
                    "mixing_mu": case["mixing_mu"], "graph_preparation_seconds": preparation,
                    "timeout_seconds": timeout,
                })
                row.update(stats)
                options = {"reference": reference} if reference is not None else {}
                row.update(run_trial(dataset.graph, dataset.truth, algorithm, algorithm_seed, timeout, **options))
                yield row


def summarize(raw: pd.DataFrame) -> pd.DataFrame:
    """Summarise successful outcomes with sample SD and retain every attempt."""
    rows = []
    for keys, group in raw.groupby(GROUP + ["algorithm"], dropna=False):
        row = dict(zip(GROUP + ["algorithm"], keys))
        valid = group[group.status == "ok"]
        maximal = valid.final_maximality.dropna()
        checked = group.final_maximality.dropna()
        row.update(
            n_attempted=len(group), n_ok=len(valid), n_timeout=int((group.status == "timeout").sum()),
            n_other_failure=int((~group.status.isin(["ok", "timeout"])).sum()),
            completion_rate=len(valid) / len(group),
            n_maximal_checked=len(checked), n_final_maximal=int(maximal.sum()),
            average_degree_mean=group.average_degree.mean(), mixing_mu_realized_mean=group.mixing_mu_realized.mean(),
        )
        for metric in MEASURES:
            values = pd.to_numeric(valid[metric], errors="raise")
            row[f"{metric}_mean"] = values.mean()
            row[f"{metric}_sd"] = values.std(ddof=1)
        rows.append(row)
    return pd.DataFrame(rows)


def paired_summary(raw: pd.DataFrame) -> pd.DataFrame:
    """Pair every comparator with FIFO FLPA on the same graph and seed."""
    rows = []
    pairing = ["graph_seed", "algorithm_seed", "graph_sha256"]
    for keys, group in raw.groupby(GROUP, dropna=False):
        control = group[group.algorithm == "flpa"]
        for algorithm, variant in group[group.algorithm != "flpa"].groupby("algorithm"):
            matched = variant.merge(control, on=pairing, suffixes=("_variant", "_fifo"), validate="one_to_one")
            valid = matched[(matched.status_variant == "ok") & (matched.status_fifo == "ok")]
            times = valid[valid.runtime_seconds_fifo > 0]
            ratios = times.runtime_seconds_variant / times.runtime_seconds_fifo
            ratio_of_means = (times.runtime_seconds_variant.mean() / times.runtime_seconds_fifo.mean()
                              if len(times) else None)
            row = dict(zip(GROUP, keys))
            row.update(algorithm=algorithm, n_pairs=len(matched), n_paired_ok=len(valid),
                       speedup_mean=ratios.mean(), speedup_sd=ratios.std(ddof=1),
                       ratio_of_paired_means=ratio_of_means)
            for metric in ("node_visits", "nmi", "ari", "acc", "n_predicted_clusters"):
                change = (pd.to_numeric(valid[f"{metric}_variant"])
                          - pd.to_numeric(valid[f"{metric}_fifo"]))
                row[f"{metric}_delta_mean"] = change.mean()
                row[f"{metric}_delta_sd"] = change.std(ddof=1)
            rows.append(row)
    return pd.DataFrame(rows)


def environment(root: Path) -> dict:
    """Capture the benchmark environment and source identity without credentials."""
    def command(args):
        try:
            return subprocess.check_output(args, cwd=root, stderr=subprocess.DEVNULL, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            return None

    return {
        "utc_time": datetime.now(timezone.utc).isoformat(),
        "os": platform.platform(), "arch": platform.machine(), "logical_cpus": os.cpu_count(),
        "cpu_model": (os.environ.get("FLPA_CPU_MODEL") or
                      command(["sysctl", "-n", "machdep.cpu.brand_string"]) or platform.processor()),
        "memory_bytes": os.environ.get("FLPA_MEMORY_BYTES") or command(["sysctl", "-n", "hw.memsize"]),
        "thread_environment": {key: os.environ.get(key) for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS")},
        "python": platform.python_version(),
        "packages": {name: version(name) for name in (
            "numpy", "scipy", "scikit-learn", "networkx", "pandas", "igraph", "leidenalg", "matplotlib", "marimo", "wandb",
        )},
        "source_commit": command(["git", "rev-parse", "HEAD"]),
        "source_changes": command([
            "git", "status", "--porcelain", "--untracked-files=all", "--", "src", "configs", "scripts",
            "pyproject.toml", "requirements.txt",
        ]),
    }
