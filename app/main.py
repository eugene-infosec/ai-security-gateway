from __future__ import annotations

import time
from uuid import uuid4
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.logger import log_safe
from app.middleware.request_id import RequestIdMiddleware
from app.auth import get_principal, Principal, Role
from app.policy import is_allowed, Classification
# NEW IMPORTS
from app.models import IngestRequest, StoredDoc, utcnow
from app.store import STORE

app = FastAPI(title="AI Security Gateway")

app.add_middleware(RequestIdMiddleware)

@app.get("/health")
def health(request: Request):
    return {"ok": True, "request_id": getattr(request.state, "request_id", None)}

@app.get("/whoami")
def whoami(principal: Principal = Depends(get_principal)):
    return principal.model_dump()

# --- NEW: HELPER ---
def _parse_classification(raw: str | None) -> Classification:
    if raw is None or str(raw).strip() == "":
        return Classification.internal
    try:
        return Classification(str(raw).strip().lower())
    except Exception:
        raise HTTPException(status_code=400, detail={"reason_code": "INVALID_CLASSIFICATION"})

# --- NEW: INGEST ENDPOINT ---
@app.post("/ingest")
def ingest(payload: IngestRequest, principal: Principal = Depends(get_principal)):
    # 1. Anti-spoofing Trap: tenant must NEVER come from request JSON
    if payload.tenant_id is not None:
        raise HTTPException(status_code=400, detail={"reason_code": "TENANT_FIELD_FORBIDDEN"})

    cls = _parse_classification(payload.classification)

    # 2. Role-bounded classification authority
    # Interns cannot label data as 'admin'
    if cls == Classification.admin and principal.role != Role.admin:
        raise HTTPException(status_code=403, detail={"reason_code": "CLASSIFICATION_FORBIDDEN"})

    # 3. Create the Stored Document (Authority Derivation happens here)
    doc = StoredDoc(
        doc_id=str(uuid4()),
        tenant_id=principal.tenant_id,  # <--- Derived from Principal, not payload
        title=payload.title,
        body=payload.body,
        classification=cls,
        created_at=utcnow(),
    )
    STORE.put_doc(doc)

    # 4. Safe Audit Log
    log_safe({
        "event": "doc_ingested",
        "tenant_id": principal.tenant_id,
        "role": principal.role.value,
        "doc_ids": [doc.doc_id],
        "classification": doc.classification.value
    })

    return {
        "doc_id": doc.doc_id,
        "tenant_id": doc.tenant_id,
        "classification": doc.classification.value,
    }

# ... (Keep existing logging middleware and exception handlers)
@app.middleware("http")
async def access_log(request: Request, call_next):
    start = time.perf_counter()
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        latency_ms = int((time.perf_counter() - start) * 1000)
        status = getattr(response, "status_code", 500)
        log_safe({
            "event": "http_request",
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "status": status,
            "latency_ms": latency_ms,
        })

@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    log_safe({
        "event": "unhandled_exception",
        "request_id": getattr(request.state, "request_id", None),
        "method": request.method,
        "path": request.url.path,
        "status": 500,
        "latency_ms": 0,
        "error": "internal_error"
    })
    return JSONResponse(status_code=500, content={"error": "internal_error"})