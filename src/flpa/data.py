"""Sparse synthetic graphs for E1 and E3 with separate evaluation labels."""

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from .graph import Graph


@dataclass(frozen=True)
class Dataset:
    """Common clustering topology and optional truth in the same node order."""

    graph: Graph
    truth: Optional[Tuple[int, ...]] = None


def sbm(n_nodes: int, degree: float, blocks: int, mu: float, seed: int) -> Dataset:
    """Sample an exact Bernoulli SBM with equal-size blocks and no self-loops.

    For each block pair draw a binomial edge count, then uniformly sample
    distinct edge ranks conditional on that count. This avoids a dense matrix.
    """
    if not 0 < blocks <= n_nodes or n_nodes % blocks:
        raise ValueError("SBM requires a positive number of equal-size blocks")
    if not 0 <= mu <= 1 or not 0 <= degree <= n_nodes - 1:
        raise ValueError("invalid SBM mixing parameter or expected degree")

    size = n_nodes // blocks
    within_degree, between_degree = (1 - mu) * degree, mu * degree
    if within_degree > size - 1 or between_degree > n_nodes - size:
        raise ValueError("requested degree and mixing imply an edge probability above 1")
    p_in = within_degree / (size - 1) if size > 1 else 0.0
    p_out = between_degree / (n_nodes - size) if blocks > 1 else 0.0

    rng = np.random.default_rng(seed)
    starts = np.arange(size, dtype=np.int64)
    starts = starts * (2 * size - starts - 1) // 2

    def edges():
        for a in range(blocks):
            for b in range(a, blocks):
                within = a == b
                candidates = size * (size - 1) // 2 if within else size * size
                count = rng.binomial(candidates, p_in if within else p_out)
                if count == 0:
                    continue
                ranks = rng.choice(candidates, count, replace=False, shuffle=False)
                if within:
                    left = np.searchsorted(starts, ranks, side="right") - 1
                    right = left + 1 + ranks - starts[left]
                else:
                    left, right = np.divmod(ranks, size)
                yield from zip((left + a * size).tolist(), (right + b * size).tolist())

    graph = Graph.from_edges(range(n_nodes), edges())
    return Dataset(graph, tuple(node // size for node in range(n_nodes)))


def generate_graph(config: dict, seed: int) -> Dataset:
    """Create ER, BA or equal-size SBM using the given graph seed."""
    name = config["dataset"]
    size = config["n_nodes"]
    degree = config["average_degree"]
    if size < 2 or not 0 <= degree <= size - 1:
        raise ValueError("invalid graph size or expected degree")
    if name == "sbm":
        return sbm(size, degree, config["n_communities"], config["mixing_mu"], seed)

    import networkx as nx

    if name == "er":
        generated = nx.fast_gnp_random_graph(size, degree / (size - 1), seed=seed)
    elif name == "ba":
        m = int(degree / 2 + 0.5)
        if m < 1:
            raise ValueError("BA requires at least one attachment per new node")
        generated = nx.barabasi_albert_graph(size, m, seed=seed)
    else:
        raise ValueError(f"unknown dataset: {name}")
    return Dataset(Graph.from_edges(range(size), generated.edges))


def graph_statistics(dataset: Dataset) -> dict:
    """Measure realised mean degree, mixing, isolates and topology fingerprint."""
    graph, truth = dataset.graph, dataset.truth
    mu = None
    if truth is not None and graph.n_edges:
        mu = sum(truth[u] != truth[v] for u, v in graph.edges()) / graph.n_edges
    return {
        "n_nodes": graph.n_nodes,
        "n_edges": graph.n_edges,
        "n_isolates": sum(not adjacency for adjacency in graph.neighbors),
        "n_communities_true": len(set(truth)) if truth is not None else None,
        "average_degree": 2 * graph.n_edges / graph.n_nodes if graph.n_nodes else None,
        "mixing_mu_realized": mu,
        "graph_sha256": graph.topology_sha256(),
    }
