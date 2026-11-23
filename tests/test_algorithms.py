from itertools import combinations

import networkx as nx
import pytest

from flpa import Graph, detect_communities, labels_are_maximal
from flpa.algorithms import PYTHON_ALGORITHMS
from flpa.data import sbm


def examples():
    two_cliques = list(combinations(range(6), 2)) + list(combinations(range(6, 12), 2))
    return [
        ("clique", Graph.from_networkx(nx.complete_graph(10))),
        ("path", Graph.from_networkx(nx.path_graph(14))),
        ("star", Graph.from_networkx(nx.star_graph(14))),
        ("cycle", Graph.from_networkx(nx.cycle_graph(15))),
        ("isolates", Graph.from_edges((10, 20, 70), [])),
        ("disconnected", Graph.from_edges((10, 20, 70, 90, 120), [(10, 20), (70, 90)])),
        ("two communities", Graph.from_edges(range(12), two_cliques + [(0, 6)])),
        ("sbm", sbm(60, 7, 3, 0.4, 21).graph),
        ("empty", Graph.from_edges([], [])),
    ]


@pytest.mark.parametrize("algorithm", PYTHON_ALGORITHMS)
@pytest.mark.parametrize("name,graph", examples(), ids=[name for name, _ in examples()])
def test_termination_and_maximality(algorithm, name, graph):
    result = detect_communities(graph, algorithm, 42, max_visits=50_000)
    assert result.status == "ok"
    assert len(result.labels) == graph.n_nodes
    assert result.label_updates <= result.update_visits <= result.node_visits
    assert labels_are_maximal(graph, result.labels)
    for node, neighbors in enumerate(graph.neighbors):
        if not neighbors:
            assert result.labels[node] == node
            continue
        labels = [result.labels[neighbor] for neighbor in neighbors]
        assert labels.count(result.labels[node]) == max(labels.count(label) for label in labels)
    if name in ("clique", "star"):
        assert len(set(result.labels)) == 1
    if name == "disconnected":
        assert len(set(result.labels)) == 3


@pytest.mark.parametrize("algorithm", PYTHON_ALGORITHMS)
def test_reproducible_seed(algorithm):
    graph = sbm(120, 9, 4, 0.45, 42).graph
    first, second = (detect_communities(graph, algorithm, 77) for _ in range(2))
    assert (first.labels, first.node_visits, first.label_updates) == (
        second.labels, second.node_visits, second.label_updates,
    )


def test_lpa_flpa_draw_from_ties_while_retention_keeps_maximal_label(monkeypatch):
    class LastTie:
        def __init__(self, seed):
            pass

        def shuffle(self, order):
            pass

        def choice(self, choices):
            return choices[-1]

    monkeypatch.setattr("flpa.algorithms.Random", LastTie)
    graph = Graph.from_networkx(nx.path_graph(3))
    lpa = detect_communities(graph, "lpa", 1)
    retention = detect_communities(graph, "retention_lpa", 1)
    flpa = detect_communities(graph, "flpa", 1)
    assert lpa.labels == flpa.labels == (2, 2, 2)
    assert retention.labels == (1, 1, 1)
    assert lpa.check_visits == 4
    assert retention.check_visits == flpa.check_visits == 0
    assert flpa.requeues == 1
    assert flpa.update_visits == flpa.requeues + graph.n_nodes


@pytest.mark.parametrize("algorithm", PYTHON_ALGORITHMS)
def test_limits_do_not_signal_convergence(algorithm):
    graph = Graph.from_networkx(nx.path_graph(8))
    capped = detect_communities(graph, algorithm, 5, max_visits=1)
    timed_out = detect_communities(graph, algorithm, 5, timeout=1e-12)
    assert capped.status == "visit_limit" and capped.node_visits == 1
    assert timed_out.status == "timeout"


def test_maximality_rejects_invalid_partitions():
    graph = Graph.from_networkx(nx.path_graph(3))
    assert not labels_are_maximal(graph, [0, 1, 2])
    with pytest.raises(ValueError, match="one label"):
        labels_are_maximal(graph, [0, 1])
