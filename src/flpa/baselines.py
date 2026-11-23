"""Library Leiden adapter and isolated comparison with the paper's igraph."""

import subprocess
from importlib.metadata import version
from time import perf_counter

from .algorithms import DetectionResult
from .graph import Graph


AUTHOR_COMMIT = "b89649877e15a2a4d3ca199c9190fe3dc181c643"


def to_igraph(graph: Graph):
    """Create an igraph with the common indices and isolates intact."""
    import igraph

    return igraph.Graph(n=graph.n_nodes, edges=list(graph.edges()), directed=False)


def run_leiden(graph, seed: int) -> DetectionResult:
    """Optimise unweighted modularity at resolution 1 with two Leiden iterations."""
    import leidenalg

    backend = f"leidenalg/{version('leidenalg')}+igraph/{version('igraph')}"
    start = perf_counter()
    if graph.ecount():
        partition = leidenalg.find_partition(
            graph, leidenalg.ModularityVertexPartition, seed=seed, n_iterations=2,
        )
        labels = tuple(partition.membership)
    else:
        labels = tuple(range(graph.vcount()))
    return DetectionResult(labels, perf_counter() - start, "ok", backend)


def run_author_reference(binary, graph: Graph, algorithm: str, seed: int, timeout: float) -> DetectionResult:
    """Execute the pinned external C backend for comparison on identical edges."""
    edge_list = f"{graph.n_nodes} {graph.n_edges}\n" + "".join(f"{u} {v}\n" for u, v in graph.edges())
    backend = f"igraph-author/{AUTHOR_COMMIT[:10]}"
    try:
        result = subprocess.run(
            [str(binary), algorithm, str(seed)], input=edge_list, capture_output=True,
            text=True, timeout=timeout, check=True,
        )
    except subprocess.TimeoutExpired:
        return DetectionResult((), timeout, "timeout", backend)
    runtime, membership = result.stdout.splitlines()
    labels = tuple(map(int, membership.split()))
    return DetectionResult(labels, float(runtime), "ok", backend)
