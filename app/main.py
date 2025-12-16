from __future__ import annotations

import uuid
from fastapi import FastAPI, Request

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
    # Proof of Identity Context (foundation for Phase 2)
    return {
        "user_id": request.headers.get("X-User", "anonymous"),
        "tenant_id": request.headers.get("X-Tenant", "unknown"),
        "role": request.headers.get("X-Role", "unknown"),
        "request_id": request.state.request_id,
    }
