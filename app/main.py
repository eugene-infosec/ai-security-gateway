from __future__ import annotations

import uuid
from fastapi import FastAPI, Request
from app.models import IngestRequest, IngestResponse
from app.security.principal import resolve_principal_from_headers
from app.security.audit import audit
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
    # 1. Resolve Identity
    p = resolve_principal_from_headers(request.headers)

    # 2. Authorize (Auth-Before-Action)
    authorize_ingest(
        principal=p,
        classification=payload.classification,
        request_id=request.state.request_id,
        path=str(request.url.path),
    )

    # 3. Action (Mock storage for now)
    doc_id = str(uuid.uuid4())
    audit(
        "doc_ingested",
        doc_id=doc_id,
        classification=payload.classification,
        request_id=request.state.request_id,
    )

    return IngestResponse(doc_id=doc_id, request_id=request.state.request_id)
