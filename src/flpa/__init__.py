"""Community detection on sparse, undirected graphs."""

from .algorithms import DetectionResult, detect_communities, labels_are_maximal
from .graph import Graph

__all__ = ["DetectionResult", "Graph", "detect_communities", "labels_are_maximal"]
