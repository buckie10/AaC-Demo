from abc import ABC, abstractmethod
from rdflib import Graph


class ArchitectureRepository(ABC):
    @abstractmethod
    def authoritative_graph(self) -> Graph: ...


class InMemoryArchitectureRepository(ArchitectureRepository):
    def __init__(self, graph: Graph):
        self.graph = graph

    def authoritative_graph(self) -> Graph:
        return self.graph
