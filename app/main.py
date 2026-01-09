import logging
import os
import sys
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from mangum import Mangum

# 1. Configure logging immediately
from app.json_logger import request_id_ctx, setup_logging

setup_logging()

# 2. Late imports to avoid circular deps or logging issues
from app.models import (  # noqa: E402
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResult,
    QueryResponse,
)
from app.security.audit import audit, sha256_hex  # noqa: E402
from app.security.jwt_claims import get_jwt_claims_from_asgi_scope  # noqa: E402
from app.security.policy import authorize_ingest  # noqa: E402
from app.security.principal import (  # noqa: E402
    resolve_principal_from_headers,
    resolve_principal_from_jwt_claims,
)
from app.security.redact import redact_text  # noqa: E402
from app.settings import ALLOW_INSECURE_HEADERS, AUTH_MODE  # noqa: E402
from app.store import STORE  # noqa: E402

logger = logging.getLogger("app.main")
access_logger = logging.getLogger("app.access")


# -----------------------------------------------------------------------------
# Lifespan (Startup/Shutdown) Logic
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Context Manager.
    Performs critical security configuration checks before the app starts.
    """
    # Fail-Closed Check
    if AUTH_MODE == "headers" and not ALLOW_INSECURE_HEADERS:
        logger.critical(
            "FATAL: AUTH_MODE='headers' requires ALLOW_INSECURE_HEADERS=true"
        )
        sys.exit(1)

    if AUTH_MODE not in ("jwt", "headers"):
        logger.critical(f"FATAL: Unknown AUTH_MODE '{AUTH_MODE}'")
        sys.exit(1)

    logger.info(f"startup_check_passed mode={AUTH_MODE}")

    yield
    # (Cleanup logic would go here)


app = FastAPI(title="AI Security Gateway", lifespan=lifespan)


# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------
def _derive_request_id(request: Request) -> str:
    """Prefer a safe upstream X-Request-Id; otherwise generate a UUID4."""
    # Simple alphanumeric + symbols check to prevent log injection via header
    raw = request.headers.get("X-Request-Id", "").strip()

    # CRITICAL FIX: Ensure 'raw' is not empty before returning it.
    # An empty string is falsy, so checking "if raw" prevents returning ""
    if raw and len(raw) < 64 and all(c.isalnum() or c in "-_." for c in raw):
        return raw

    return str(uuid.uuid4())


def resolve_principal(request: Request):
    """
    Fail-closed principal resolution.
    """
    if AUTH_MODE == "jwt":
        claims = get_jwt_claims_from_asgi_scope(request.scope)
        if not claims:
            raise HTTPException(status_code=401, detail="Missing/invalid JWT")
        return resolve_principal_from_jwt_claims(claims)

    if AUTH_MODE == "headers":
        # Double-check environment configuration
        if not ALLOW_INSECURE_HEADERS:
            raise HTTPException(
                status_code=500,
                detail="Server Misconfiguration: insecure headers blocked",
            )
        return resolve_principal_from_headers(request.headers)

    # Should be unreachable due to startup check, but safe default:
    raise HTTPException(status_code=500, detail="Server Authentication Misconfigured")


# -----------------------------------------------------------------------------
# Middleware: Request ID + Access Logging
# -----------------------------------------------------------------------------
@app.middleware("http")
async def request_context(request: Request, call_next):
    rid = _derive_request_id(request)

    # 1. Set ContextVar for correlation in deep calls (e.g. audit logs)
    token = request_id_ctx.set(rid)
    request.state.request_id = rid

    start = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code

        # ---------------------------------------------------------
        # TRACE CORRELATION SIGNAL
        # ---------------------------------------------------------
        response.headers["X-Request-Id"] = rid
        response.headers["X-Trace-Id"] = rid  # <--- NEW: Alias for client correlation

        return response
    except Exception:
        status_code = 500
        raise
    finally:
        duration_ms = int((time.perf_counter() - start) * 1000)

        # 2. Structured Access Log
        access_logger.info(
            "request_complete",
            extra={
                "props": {
                    "event": "request_complete",
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "duration_ms": duration_ms,
                }
            },
        )

        # 3. Cleanup ContextVar
        request_id_ctx.reset(token)


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.get("/health")
def health(request: Request):
    return {"ok": True, "request_id": request.state.request_id}


@app.get("/whoami")
def whoami(request: Request):
    p = resolve_principal(request)
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
        "auth_mode": AUTH_MODE,
        "request_id": request.state.request_id,
    }


@app.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest, request: Request):
    p = resolve_principal(request)

    authorize_ingest(
        principal=p,
        classification=payload.classification,
        request_id=request.state.request_id,
        path=str(request.url.path),
    )

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
    p = resolve_principal(request)

    # 1) Scope calculation (Auth-Before-Retrieval)
    allowed = {"public", "admin"} if p.role == "admin" else {"public"}

    candidates = STORE.list_scoped(
        tenant_id=p.tenant_id, allowed_classifications=allowed
    )

    # 2) Ranking (Simple Keyword Match)
    q = payload.query.strip().lower()
    if not q:
        return QueryResponse(results=[], request_id=request.state.request_id)

    ranked = [d for d in candidates if q in d.body.lower()]

    # 3) Projection & Redaction (Redact-Before-Return)
    results = [
        QueryResult(
            doc_id=d.doc_id,
            title=redact_text(d.title),
            snippet=redact_text(d.body)[:160],
        )
        for d in ranked
    ]

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

    return QueryResponse(results=results, request_id=request.state.request_id)


# -----------------------------------------------------------------------------
# Lambda Handler
# -----------------------------------------------------------------------------
stage = os.environ.get("ENV", "dev").strip()
root_path = f"/{stage}" if stage else ""
handler = Mangum(app, api_gateway_base_path=root_path)
