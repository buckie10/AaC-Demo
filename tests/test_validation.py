from pathlib import Path
import yaml
from fastapi.testclient import TestClient
from rdflib import Graph, Namespace, RDF
from src.app import app

ROOT = Path(__file__).parents[1]


def client_with_local_authority(monkeypatch):
    graph = Graph().parse(ROOT / "semantic/ontology.ttl", format="turtle")
    graph.parse(ROOT / "semantic/canonical_world.ttl", format="turtle")
    monkeypatch.setattr("src.app.repository", type("LocalRepo", (), {
        "authoritative_graph": lambda self: graph,
        "ready": lambda self: True,
    })())
    return TestClient(app)


def post_manifest(client, name):
    with (ROOT / "manifests" / name).open() as handle:
        return client.post("/architecture/assertions", json=yaml.safe_load(handle))


def test_three_supplied_scenarios(monkeypatch):
    client = client_with_local_authority(monkeypatch)
    assert post_manifest(client, "valid_intra_domain.yaml").status_code == 200
    invalid = post_manifest(client, "invalid_cross_domain_db.yaml")
    assert invalid.status_code == 422
    assert invalid.json()["violations"][0]["code"] == "ARCH-DATA-001"
    assert invalid.json()["violations"][0]["sourceDomain"] == "FC"
    assert invalid.json()["violations"][0]["targetDomain"] == "RC"
    assert post_manifest(client, "valid_cross_domain_api.yaml").status_code == 200


def test_unknown_references_and_malformed_manifest(monkeypatch):
    client = client_with_local_authority(monkeypatch)
    unknown = {"manifestVersion": "1.0", "deployment": {"id": "x", "application": "NOPE", "components": []}}
    assert client.post("/architecture/assertions", json=unknown).status_code == 404
    assert client.post("/architecture/assertions", json={}).status_code == 400


def test_multiple_connections_return_all_policy_results(monkeypatch):
    client = client_with_local_authority(monkeypatch)
    ea = Namespace("https://example.org/architecture/ontology#")
    ent = Namespace("https://example.org/architecture/entity/")
    from src.app import repository
    repository.authoritative_graph().add((ent["RC-SECOND-DB"], RDF.type, ea.Database))
    repository.authoritative_graph().add((ent["RC-SECOND-DB"], ea.databaseOf, ent["RC-CM"]))
    manifest = yaml.safe_load((ROOT / "manifests/invalid_cross_domain_db.yaml").read_text())
    manifest["deployment"]["components"][0]["connections"].append({"mode": "direct-database", "target": "RC-SECOND-DB"})
    response = client.post("/architecture/assertions", json=manifest)
    assert response.status_code == 422
    assert len(response.json()["violations"]) == 2
