from __future__ import annotations

import uuid
from fastapi import FastAPI, Request

# Consolidated imports
from app.models import (
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    QueryResult,
)
from app.store import STORE
from app.security.principal import resolve_principal_from_headers
from app.security.audit import audit, sha256_hex
from app.security.policy import authorize_ingest

app = FastAPI(title="AI Security Gateway")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    # 1. Generate Correlation ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # 2. Process Request
    response = await call_next(request)

    # 3. Return ID header
    response.headers["X-Request-Id"] = request_id
    return response


@app.get("/health")
def health(request: Request):
    return {"ok": True, "request_id": request.state.request_id}


@app.get("/whoami")
def whoami(request: Request):
    p = resolve_principal_from_headers(request.headers)
    audit(
        "identity_resolved",
        user_id=p.user_id,
        tenant_id=p.tenant_id,
        role=p.role,
        request_id=request.state.request_id,
    )
    return {
        "user_id": p.user_id,
        "tenant_id": p.tenant_id,
        "role": p.role,
        "request_id": request.state.request_id,
    }


@app.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest, request: Request):
    p = resolve_principal_from_headers(request.headers)

    # 1. Authorize
    authorize_ingest(
        principal=p,
        classification=payload.classification,
        request_id=request.state.request_id,
        path=str(request.url.path),
    )

    # 2. Store (In-Memory)
    doc = STORE.put(
        tenant_id=p.tenant_id,
        classification=payload.classification,
        title=payload.title,
        body=payload.body,
    )

    audit(
        "doc_ingested",
        doc_id=doc.doc_id,
        classification=doc.classification,
        request_id=request.state.request_id,
    )
    return IngestResponse(doc_id=doc.doc_id, request_id=request.state.request_id)


@app.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest, request: Request):
    p = resolve_principal_from_headers(request.headers)

    # 1. Scope Calculation (Auth-Before-Retrieval)
    allowed = {"public", "admin"} if p.role == "admin" else {"public"}

    # 2. Scoped Fetch (The Invariant)
    scoped_docs = STORE.list_scoped(
        tenant_id=p.tenant_id, allowed_classifications=allowed
    )

    # 3. In-Memory Search (Lexical)
    q = payload.query.strip().lower()
    tokens = [t for t in q.split() if t]

    def score(doc):
        text = (doc.title + " " + doc.body).lower()
        return sum(text.count(t) for t in tokens)

    ranked = sorted(scoped_docs, key=score, reverse=True)
    ranked = [d for d in ranked if score(d) > 0][:10]

    # 4. Result Projection
    results = [
        QueryResult(
            doc_id=d.doc_id,
            title=d.title,
            snippet=d.body[:160],
        )
        for d in ranked
    ]

    # 5. Safe Audit
    audit(
        "query_allowed",
        tenant_id=p.tenant_id,
        role=p.role,
        user_id=p.user_id,
        request_id=request.state.request_id,
        query_sha256=sha256_hex(payload.query),
        query_len=len(payload.query),
        results_count=len(results),
        doc_ids=[r.doc_id for r in results],
    )

    return QueryResponse(request_id=request.state.request_id, results=results)
