import logging
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from rdflib import Namespace, RDF
from .models import Manifest
from .rdf_mapper import EA, ENT, candidate_graph, serialize_graph
from .fuseki_repository import FusekiArchitectureRepository
from .validation import validate_candidate

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","message":"%(message)s"}')
log = logging.getLogger("assertion-api")
app = FastAPI(title="Architecture Assertion API", version="0.1.0")
repository = FusekiArchitectureRepository(os.getenv("FUSEKI_URL", "http://localhost:3030/architecture"))


@app.exception_handler(RequestValidationError)
async def malformed_manifest(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"error": "malformed_manifest", "details": exc.errors()})


@app.get("/health")
def health():
    ready = repository.ready()
    return {"status": "ok" if ready else "starting", "ready": ready}


@app.post("/architecture/assertions")
def assert_architecture(manifest: Manifest):
    assertion_id = manifest.deployment.id
    log.info("assertion received id=%s", assertion_id)
    authoritative = repository.authoritative_graph()
    application = ENT[manifest.deployment.application]
    if (application, RDF.type, EA.Application) not in authoritative:
        raise HTTPException(404, detail={"error": "unknown_architecture_reference", "reference": manifest.deployment.application})
    for component in manifest.deployment.components:
        for connection in component.connections:
            if connection.mode not in ("direct-database", "api"):
                raise HTTPException(400, detail={"error": "unsupported_connection_mode", "mode": connection.mode})
            target = ENT[connection.target]
            target_type = EA.Database if connection.mode == "direct-database" else EA.API
            if (target, RDF.type, target_type) not in authoritative:
                raise HTTPException(404, detail={"error": "unknown_architecture_reference", "reference": connection.target})
    log.info("architecture references resolved id=%s", assertion_id)
    candidate = candidate_graph(manifest)
    log.info("candidate RDF created id=%s triples=%d", assertion_id, len(candidate))
    log.info("SHACL validation started id=%s", assertion_id)
    violations, shacl_report, policies = validate_candidate(authoritative, candidate)
    evidence = {
        "candidateRdf": serialize_graph(candidate),
        "authoritativeContextRdf": serialize_graph(authoritative),
        "shaclReportRdf": shacl_report.serialize(format="turtle"),
    }
    evaluation = {
        "policyCodes": [policy["code"] for policy in policies],
        "sourceShapes": [policy["sourceShape"] for policy in policies],
        "policies": policies,
    }
    if violations:
        log.info("SHACL validation failed id=%s codes=%s", assertion_id, [v["code"] for v in violations])
        return JSONResponse(status_code=422, content={"status": "rejected", "conforms": False, "assertionId": assertion_id, "violations": violations, "evidence": evidence, "evaluation": evaluation})
    log.info("SHACL validation passed id=%s", assertion_id)
    return {"status": "accepted", "conforms": True, "assertionId": assertion_id, "violations": [], "evidence": evidence, "evaluation": evaluation}
