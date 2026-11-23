"""Partition statistics evaluated after stopping the algorithm timer."""

from collections import Counter
from typing import Sequence

from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.metrics.cluster import contingency_matrix

from .graph import Graph


def clustering_accuracy(truth: Sequence[int], labels: Sequence[int]) -> float:
    """Return Hungarian-matched ACC, including rectangular contingency tables."""
    if not len(truth) or len(truth) != len(labels):
        raise ValueError("accuracy requires nonempty aligned label arrays")
    counts = contingency_matrix(truth, labels)
    rows, columns = linear_sum_assignment(counts, maximize=True)
    return float(counts[rows, columns].sum() / len(truth))


def modularity(graph: Graph, labels: Sequence[int]):
    """Return unweighted Newman–Girvan Q at resolution 1, or None for m=0."""
    if len(labels) != graph.n_nodes:
        raise ValueError("expected one label per vertex")
    if not graph.n_edges:
        return None
    degrees = Counter()
    for label, adjacency in zip(labels, graph.neighbors):
        degrees[label] += len(adjacency)
    internal_edges = sum(labels[u] == labels[v] for u, v in graph.edges())
    return internal_edges / graph.n_edges - sum(
        (degree / (2 * graph.n_edges)) ** 2 for degree in degrees.values()
    )


def evaluate_partition(graph: Graph, labels: Sequence[int], truth=None) -> dict:
    """Return topology scores and, if truth is known, NMI, ARI and ACC."""
    scores = {
        "n_predicted_clusters": len(set(labels)),
        "modularity": modularity(graph, labels),
        "nmi": None,
        "ari": None,
        "acc": None,
    }
    if truth is not None and len(truth):
        scores.update(
            nmi=float(normalized_mutual_info_score(truth, labels, average_method="arithmetic")),
            ari=float(adjusted_rand_score(truth, labels)),
            acc=clustering_accuracy(truth, labels),
        )
    return scores
