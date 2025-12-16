from __future__ import annotations

import uuid
from fastapi import FastAPI, Request
from app.security.principal import resolve_principal_from_headers
from app.security.audit import audit

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
    # 1. Resolve Identity
    p = resolve_principal_from_headers(request.headers)

    # 2. Audit the access (Proof of Audit)
    audit(
        "identity_resolved",
        user_id=p.user_id,
        tenant_id=p.tenant_id,
        role=p.role,
        request_id=request.state.request_id,
    )

    # 3. Return context
    return {
        "user_id": p.user_id,
        "tenant_id": p.tenant_id,
        "role": p.role,
        "request_id": request.state.request_id,
    }
