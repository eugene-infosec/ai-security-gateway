from __future__ import annotations

import time
from uuid import uuid4
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.audit import emit_audit_event
from app.logger import log_safe
from app.middleware.request_id import RequestIdMiddleware
from app.auth import get_principal, Principal, Role
from app.policy import is_allowed, Classification, allowed_classifications
from app.models import IngestRequest, StoredDoc, utcnow, QueryRequest, QueryResult
from app.store import STORE
from app.search import tokenize, score_doc
from app.snippet import make_snippet

app = FastAPI(title="AI Security Gateway")

app.add_middleware(RequestIdMiddleware)

@app.get("/health")
def health(request: Request):
    return {"ok": True, "request_id": getattr(request.state, "request_id", None)}

@app.get("/whoami")
def whoami(principal: Principal = Depends(get_principal)):
    return principal.model_dump()

# --- HELPER ---
def _parse_classification(raw: str | None) -> Classification:
    if raw is None or str(raw).strip() == "":
        return Classification.internal
    try:
        return Classification(str(raw).strip().lower())
    except Exception:
        raise HTTPException(status_code=400, detail={"reason_code": "INVALID_CLASSIFICATION"})

# --- INGEST ENDPOINT ---
@app.post("/ingest")
def ingest(payload: IngestRequest, principal: Principal = Depends(get_principal)):
    # 1. Anti-spoofing Trap
    if payload.tenant_id is not None:
        raise HTTPException(status_code=400, detail={"reason_code": "TENANT_FIELD_FORBIDDEN"})

    cls = _parse_classification(payload.classification)

    # 2. Role-bounded classification authority
    if cls == Classification.admin and principal.role != Role.admin:
        raise HTTPException(status_code=403, detail={"reason_code": "CLASSIFICATION_FORBIDDEN"})

    # 3. Create Stored Document
    doc = StoredDoc(
        doc_id=str(uuid4()),
        tenant_id=principal.tenant_id,
        title=payload.title,
        body=payload.body,
        classification=cls,
        created_at=utcnow(),
    )
    STORE.put_doc(doc)

    # 4. Audit Log
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

# --- QUERY ENDPOINT ---
@app.post("/query")
def query_docs(payload: QueryRequest, principal: Principal = Depends(get_principal)):
    # 1. SCOPE
    docs = STORE.list_docs(principal.tenant_id)
    allowed_cls = allowed_classifications(principal.role)

    # 2. FILTER (Auth-Before-Retrieval)
    allowed_docs = []
    for d in docs:
        m = d.model_dump(mode="json")
        try:
            cls = Classification(m.get("classification"))
        except Exception:
            continue
        
        if cls in allowed_cls:
            allowed_docs.append(m)

    # 3. RANK
    q_tokens = tokenize(payload.query)
    scored = []
    for d in allowed_docs:
        s = score_doc(d, q_tokens)
        if s > 0:
            scored.append((s, d))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[: payload.k]

    # 4. RETURN (Safe Snippets)
    results = []
    for _s, d in top:
        results.append(
            QueryResult(
                doc_id=d["doc_id"],
                title=d["title"],
                snippet=make_snippet(principal, d, payload.query),
            ).model_dump()
        )
    
    # 5. Audit
    log_safe({
        "event": "search_executed",
        "tenant_id": principal.tenant_id,
        "role": principal.role.value,
        "match_count": len(results)
    })

    return {"results": results}

# --- MIDDLEWARE & EXCEPTIONS ---

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

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Captures 403/401 errors and logs a structured Security Audit Event.
    """
    if 400 <= exc.status_code < 500:
        principal = getattr(request.state, "principal", None)
        
        reason = "UNKNOWN"
        if isinstance(exc.detail, dict):
            reason = exc.detail.get("reason_code", "UNKNOWN")
        else:
            reason = str(exc.detail)

        emit_audit_event(
            event_name="access_denied",
            principal=principal,
            reason=reason,
            extra={
                "status": exc.status_code,
                "path": request.url.path,
                "request_id": getattr(request.state, "request_id", None)
            }
        )

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail}
    )

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