import httpx
from rdflib import Graph
from .repository import ArchitectureRepository


class FusekiArchitectureRepository(ArchitectureRepository):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def authoritative_graph(self) -> Graph:
        response = httpx.get(f"{self.base_url}/data", params={"default": ""},
                             headers={"Accept": "text/turtle"}, timeout=10)
        response.raise_for_status()
        graph = Graph()
        graph.parse(data=response.text, format="turtle")
        return graph

    def ready(self) -> bool:
        try:
            self.authoritative_graph()
            return True
        except Exception:
            return False
