from rdflib import Graph, Namespace, URIRef, RDF
from .models import Manifest

EA = Namespace("https://example.org/architecture/ontology#")
ENT = Namespace("https://example.org/architecture/entity/")
DEP = Namespace("https://example.org/architecture/deployment/")


def candidate_graph(manifest: Manifest) -> Graph:
    graph = Graph()
    assertion = DEP[manifest.deployment.id]
    graph.add((assertion, RDF.type, EA.DeploymentAssertion))
    graph.add((assertion, EA.deployedApplication, ENT[manifest.deployment.application]))
    for component in manifest.deployment.components:
        for connection in component.connections:
            predicate = {"direct-database": EA.directDatabaseAccess,
                         "api": EA.apiAccess}.get(connection.mode)
            if predicate:
                graph.add((assertion, predicate, ENT[connection.target]))
    return graph


def uri_identifier(uri: URIRef) -> str:
    return str(uri).rstrip("/").rsplit("/", 1)[-1]


def serialize_graph(graph: Graph) -> str:
    graph.bind("ea", EA)
    graph.bind("ent", ENT)
    graph.bind("dep", DEP)
    return graph.serialize(format="turtle")
