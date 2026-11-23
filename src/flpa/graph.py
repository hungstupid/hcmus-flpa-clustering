"""Common topology shared by all community detection backends."""

from array import array
from dataclasses import dataclass
from hashlib import sha256
from itertools import chain
from sys import byteorder
from typing import Hashable, Iterable, Iterator, Tuple


@dataclass(frozen=True)
class Graph:
    """Immutable simple graph in the node order supplied to ``from_edges``.

    Input identifiers can be non-contiguous. Adjacency lists contain sorted
    internal indices. Explicit identifiers preserve isolates.
    """

    node_ids: Tuple[Hashable, ...]
    neighbors: Tuple[Tuple[int, ...], ...]
    n_edges: int

    @classmethod
    def from_edges(
        cls,
        node_ids: Iterable[Hashable],
        edges: Iterable[Tuple[Hashable, Hashable]],
    ) -> "Graph":
        """Index explicit vertices and unique undirected edges; reject loops."""
        ids = tuple(node_ids)
        indices = {node: index for index, node in enumerate(ids)}
        if len(indices) != len(ids):
            raise ValueError("node identifiers must be unique")

        neighbors = [set() for _ in ids]
        for left, right in edges:
            u, v = indices[left], indices[right]
            if u == v:
                raise ValueError("self-loops require explicit preprocessing")
            neighbors[u].add(v)
            neighbors[v].add(u)
        adjacency = tuple(tuple(sorted(nodes)) for nodes in neighbors)
        return cls(ids, adjacency, sum(map(len, adjacency)) // 2)

    @classmethod
    def from_networkx(cls, graph) -> "Graph":
        """Adapt a simple undirected NetworkX graph using topology only."""
        if graph.is_directed() or graph.is_multigraph():
            raise ValueError("expected a simple undirected graph")
        return cls.from_edges(graph.nodes, graph.edges)

    @property
    def n_nodes(self) -> int:
        """Number of vertices, including isolates."""
        return len(self.node_ids)

    def edges(self) -> Iterator[Tuple[int, int]]:
        """Yield each undirected edge once in internal index order."""
        for u, neighbors in enumerate(self.neighbors):
            for v in neighbors:
                if u < v:
                    yield u, v

    def topology_sha256(self) -> str:
        """Hash the vertex count and canonical edges in index space."""
        words = array("Q", chain((self.n_nodes,), chain.from_iterable(self.edges())))
        if byteorder != "little":
            words.byteswap()
        return sha256(words).hexdigest()
