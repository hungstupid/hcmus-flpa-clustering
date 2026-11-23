"""Independent implementations of Algorithms 1–3 of Traag and Šubelj."""

from collections import deque
from dataclasses import dataclass
from math import isfinite
from random import Random
from time import perf_counter
from typing import Optional, Sequence, Tuple

from .graph import Graph


@dataclass(frozen=True)
class DetectionResult:
    """Membership in graph order and instrumentation for one execution.

    ``timeout`` and ``visit_limit`` can return a partial partition. Use
    memberships for evaluation only when ``status == 'ok'``. Native backends
    leave unsupported counters as None.
    """

    labels: Tuple[int, ...]
    runtime_seconds: float
    status: str
    backend: str
    update_visits: Optional[int] = None
    check_visits: Optional[int] = None
    label_updates: Optional[int] = None
    neighbor_examinations: Optional[int] = None
    sweeps: Optional[int] = None
    requeues: Optional[int] = None

    @property
    def node_visits(self) -> Optional[int]:
        """Vertices scored for updates plus vertices scored for stopping checks."""
        if self.update_visits is None or self.check_visits is None:
            return None
        return self.update_visits + self.check_visits


class _Stopped(Exception):
    """An execution reached its time or work budget."""


class _Work:
    def __init__(self, deadline, max_visits):
        self.deadline = deadline
        self.max_visits = max_visits
        self.update_visits = 0
        self.check_visits = 0
        self.label_updates = 0
        self.neighbor_examinations = 0
        self.sweeps = 0
        self.requeues = 0

    def visit(self, degree: int, *, check: bool = False) -> None:
        visits = self.update_visits + self.check_visits
        if self.max_visits is not None and visits >= self.max_visits:
            raise _Stopped("visit_limit")
        if self.deadline is not None and visits % 256 == 0:
            if perf_counter() >= self.deadline:
                raise _Stopped("timeout")
        if check:
            self.check_visits += 1
        else:
            self.update_visits += 1
        self.neighbor_examinations += degree


def _counts(neighbors, labels):
    counts = {}
    for neighbor in neighbors:
        label = labels[neighbor]
        counts[label] = counts.get(label, 0) + 1
    return counts


def _pick_label(counts, best_count, rng):
    best = [label for label, count in counts.items() if count == best_count]
    return best[0] if len(best) == 1 else rng.choice(best)


def labels_are_maximal(graph: Graph, labels: Sequence[int]) -> bool:
    """Test the final-label invariant on all non-isolates in graph order."""
    if len(labels) != graph.n_nodes:
        raise ValueError("expected one label for each vertex")
    for node, neighbors in enumerate(graph.neighbors):
        if neighbors:
            counts = _counts(neighbors, labels)
            if counts.get(labels[node], 0) < max(counts.values()):
                return False
    return True


def _maximal_after_sweep(graph, labels, work):
    for node, neighbors in enumerate(graph.neighbors):
        work.visit(len(neighbors), check=True)
        if neighbors:
            counts = _counts(neighbors, labels)
            if counts.get(labels[node], 0) < max(counts.values()):
                return False
    return True


def _run_sweeps(graph, labels, rng, work, *, retain):
    if not retain and graph.n_edges == 0:
        return
    order = list(range(graph.n_nodes))
    while order:
        rng.shuffle(order)
        work.sweeps += 1
        changes_before = work.label_updates
        for node in order:
            neighbors = graph.neighbors[node]
            work.visit(len(neighbors))
            if not neighbors:
                continue
            counts = _counts(neighbors, labels)
            best_count = max(counts.values())
            previous = labels[node]
            if retain and counts.get(previous, 0) == best_count:
                continue
            chosen = _pick_label(counts, best_count, rng)
            if chosen != previous:
                labels[node] = chosen
                work.label_updates += 1

        if retain:
            if work.label_updates == changes_before:
                return
        elif _maximal_after_sweep(graph, labels, work):
            return


def _run_queue(graph, labels, rng, work, *, lifo, enqueue_all):
    order = list(range(graph.n_nodes))
    rng.shuffle(order)
    queue = deque(order)
    queued = bytearray(b"\x01") * graph.n_nodes
    pop = queue.pop if lifo else queue.popleft

    while queue:
        node = pop()
        queued[node] = 0
        neighbors = graph.neighbors[node]
        work.visit(len(neighbors))
        if not neighbors:
            continue
        counts = _counts(neighbors, labels)
        chosen = _pick_label(counts, max(counts.values()), rng)
        if chosen == labels[node]:
            continue

        labels[node] = chosen
        work.label_updates += 1
        work.neighbor_examinations += len(neighbors)
        for neighbor in neighbors:
            if not queued[neighbor] and (enqueue_all or labels[neighbor] != chosen):
                queue.append(neighbor)
                queued[neighbor] = 1
                work.requeues += 1


PYTHON_ALGORITHMS = ("lpa", "retention_lpa", "flpa", "flpa_lifo", "flpa_all")


def detect_communities(
    graph: Graph,
    algorithm: str,
    seed: int,
    *,
    timeout: Optional[float] = None,
    max_visits: Optional[int] = None,
) -> DetectionResult:
    """Cluster a graph with a private RNG and optional cooperative budgets.

    Select ``lpa``, ``retention_lpa``, ``flpa``, ``flpa_lifo``, ``flpa_all`` or
    ``leiden``. The Python time budget is checked every 256 visits. The Leiden
    adapter needs the experiment runner if a hard wall-clock timeout is required.
    """
    if timeout is not None and (not isfinite(timeout) or timeout <= 0):
        raise ValueError("timeout must be a finite positive number of seconds")
    if max_visits is not None and max_visits <= 0:
        raise ValueError("max_visits must be positive")
    if algorithm == "leiden":
        if timeout is not None or max_visits is not None:
            raise ValueError("use the experiment runner to bound Leiden runtime")
        from .baselines import run_leiden, to_igraph

        return run_leiden(to_igraph(graph), seed)
    if algorithm not in PYTHON_ALGORITHMS:
        raise ValueError(f"unknown algorithm: {algorithm}")

    start = perf_counter()
    deadline = start + timeout if timeout is not None else None
    rng = Random(seed)
    labels = list(range(graph.n_nodes))
    work = _Work(deadline, max_visits)
    try:
        if algorithm in ("lpa", "retention_lpa"):
            _run_sweeps(graph, labels, rng, work, retain=algorithm == "retention_lpa")
        else:
            _run_queue(
                graph, labels, rng, work,
                lifo=algorithm == "flpa_lifo", enqueue_all=algorithm == "flpa_all",
            )
    except _Stopped as stopped:
        status = str(stopped)
    else:
        status = "ok"

    runtime = perf_counter() - start
    if status == "ok" and timeout is not None and runtime >= timeout:
        status = "timeout"
    return DetectionResult(
        labels=tuple(labels), runtime_seconds=runtime, status=status, backend="python",
        update_visits=work.update_visits, check_visits=work.check_visits,
        label_updates=work.label_updates, neighbor_examinations=work.neighbor_examinations,
        sweeps=work.sweeps if algorithm in ("lpa", "retention_lpa") else None,
        requeues=work.requeues if algorithm.startswith("flpa") else None,
    )
