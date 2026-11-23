import networkx as nx
import pytest

from flpa import Graph, detect_communities
from flpa.baselines import to_igraph
from flpa.data import generate_graph, graph_statistics, sbm
from flpa.metrics import clustering_accuracy, evaluate_partition, modularity


@pytest.mark.parametrize("name", ("er", "ba", "sbm"))
def test_sparse_generators_are_seeded_and_simple(name):
    config = {"dataset": name, "n_nodes": 2000, "average_degree": 10, "n_communities": 100, "mixing_mu": 0.45}
    first = generate_graph(config, 210)
    assert first == generate_graph(config, 210)
    assert first.graph.topology_sha256() != generate_graph(config, 211).graph.topology_sha256()
    stats = graph_statistics(first)
    assert stats["average_degree"] == pytest.approx(10, abs=0.3)
    edges = list(first.graph.edges())
    assert len(edges) == len(set(edges)) == first.graph.n_edges
    assert all(u < v and u in first.graph.neighbors[v] for u, v in edges)
    if name == "sbm":
        assert stats["mixing_mu_realized"] == pytest.approx(0.45, abs=0.03)
        assert stats["n_communities_true"] == 100
        assert first.truth == tuple(i // 20 for i in first.graph.node_ids)
    else:
        assert first.truth is None


def test_sbm_probability_boundaries():
    cliques = sbm(6, 2, 2, 0, 10)
    bipartite = sbm(6, 3, 2, 1, 10)
    assert cliques.graph.n_edges == 6
    assert bipartite.graph.n_edges == 9
    assert graph_statistics(bipartite)["mixing_mu_realized"] == 1
    assert sbm(5, 0, 5, 0.5, 10).graph.n_edges == 0
    with pytest.raises(ValueError, match="probability"):
        sbm(6, 4, 2, 0, 10)


def test_node_order_isolates_and_leiden_integration():
    graph = Graph.from_edges((30, 5, 100, 62), [(5, 30), (30, 5), (5, 62)])
    assert graph.node_ids == (30, 5, 100, 62)
    assert graph.neighbors == ((1,), (0, 3), (), (1,))
    backend_graph = to_igraph(graph)
    assert backend_graph.vcount() == 4
    assert set(backend_graph.get_edgelist()) == set(graph.edges())
    leiden = detect_communities(graph, "leiden", 33)
    assert leiden.status == "ok" and leiden.node_visits is None and leiden.label_updates is None
    assert leiden.labels == detect_communities(graph, "leiden", 33).labels
    assert leiden.labels[0] == leiden.labels[1] == leiden.labels[3] != leiden.labels[2]


def test_explicit_graph_normalization():
    with pytest.raises(ValueError, match="undirected"):
        Graph.from_networkx(nx.DiGraph([(1, 2)]))
    with pytest.raises(ValueError, match="self-loops"):
        Graph.from_edges([1], [(1, 1)])


def test_metrics_identical_permuted_and_different():
    graph = Graph.from_networkx(nx.path_graph(4))
    labels = [0, 0, 1, 1]
    for predictions in (labels, [10, 10, 8, 8]):
        metrics = evaluate_partition(graph, predictions, labels)
        assert metrics["nmi"] == pytest.approx(1)
        assert metrics["ari"] == pytest.approx(1)
        assert metrics["acc"] == 1
    cross = evaluate_partition(graph, [3, 7, 3, 7], labels)
    assert cross["nmi"] == pytest.approx(0)
    assert cross["ari"] == pytest.approx(-0.5)
    assert cross["acc"] == pytest.approx(0.5)
    assert evaluate_partition(graph, labels)["nmi"] is None


def test_rectangular_hungarian_and_modularity():
    assert clustering_accuracy([3, 3, 4, 4, 4], [1, 2, 7, 7, 7]) == pytest.approx(0.8)
    assert clustering_accuracy([0, 0, 1, 1], [2, 2, 2, 2]) == pytest.approx(0.5)
    with pytest.raises(ValueError):
        clustering_accuracy([0, 0], [0])
    graph = Graph.from_edges(range(4), [(0, 1), (2, 3)])
    assert modularity(graph, [0, 0, 1, 1]) == pytest.approx(0.5)
    assert modularity(graph, [0, 0, 0, 0]) == pytest.approx(0)
    assert modularity(Graph.from_edges(range(2), []), [0, 1]) is None
