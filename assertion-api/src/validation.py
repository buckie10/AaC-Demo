from pathlib import Path
from rdflib import Graph, Namespace, URIRef, RDF
from pyshacl import validate
from .rdf_mapper import EA, uri_identifier

POLICY = Namespace("https://example.org/architecture/policy#")
SH = Namespace("http://www.w3.org/ns/shacl#")


def validate_candidate(authoritative: Graph, candidate: Graph) -> list[dict]:
    combined = authoritative + candidate
    shapes_path = Path(__file__).parents[1] / "semantic" / "shapes.ttl"
    if not shapes_path.exists():
        shapes_path = Path(__file__).parents[2] / "semantic" / "shapes.ttl"
    shapes = Graph().parse(shapes_path.as_uri(), format="turtle")
    conforms, report, _ = validate(combined, shacl_graph=shapes, inference="none", advanced=True)
    if conforms:
        return []
    violations = []
    for result in report.subjects(RDF.type, SH.ValidationResult):
        source_shape = report.value(result, SH.sourceShape)
        code = shapes.value(source_shape, POLICY.errorCode)
        focus = report.value(result, SH.focusNode)
        value = report.value(result, SH.value)
        message = report.value(result, SH.resultMessage)
        source = combined.value(focus, EA.deployedApplication)
        source_domain = authoritative.value(source, EA.ownedByDomain) if source else None
        target_domain = None
        if value:
            database_app = authoritative.value(value, EA.databaseOf)
            if database_app:
                target_domain = authoritative.value(database_app, EA.ownedByDomain)
        violations.append({
            "code": str(code) if code else "SHACL-VIOLATION",
            "severity": "ERROR" if report.value(result, SH.resultSeverity) == SH.Violation else uri_identifier(report.value(result, SH.resultSeverity) or SH.Violation).upper(),
            "source": uri_identifier(source) if source else None,
            "target": uri_identifier(value) if value else None,
            "sourceDomain": uri_identifier(source_domain) if source_domain else None,
            "targetDomain": uri_identifier(target_domain) if target_domain else None,
            "message": str(message) if message else "Architecture policy violation.",
        })
    return sorted(violations, key=lambda item: (item["code"], item.get("target") or "", item.get("source") or ""))
