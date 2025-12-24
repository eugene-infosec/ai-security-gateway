import os
import re
import time
import uuid
import logging

from fastapi import FastAPI, Request, HTTPException
from mangum import Mangum

from app.json_logger import setup_logging, request_id_ctx

# Configure logging BEFORE other app imports to capture everything
setup_logging()

# noqa: E402 tells the linter to ignore "imports not at top" for these lines
from app.models import (  # noqa: E402
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    QueryResult,
)
from app.store import STORE  # noqa: E402
from app.security.audit import audit, sha256_hex  # noqa: E402
from app.security.policy import authorize_ingest  # noqa: E402
from app.security.jwt_claims import get_jwt_claims_from_asgi_scope  # noqa: E402
from app.security.redact import redact_text  # noqa: E402
from app.security.principal import (  # noqa: E402
    resolve_principal_from_headers,
    resolve_principal_from_jwt_claims,
)

logger = logging.getLogger("app.main")
access_logger = logging.getLogger("app.access")

app = FastAPI(title="AI Security Gateway")

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _derive_request_id(request: Request) -> str:
    """Prefer a safe upstream X-Request-Id; otherwise generate a UUID4."""
    rid = (request.headers.get("X-Request-Id") or "").strip()
    if rid and _REQUEST_ID_RE.match(rid):
        return rid
    return str(uuid.uuid4())


def _auth_mode() -> str:
    """
    Supported:
      - jwt      (prod)
      - headers  (local/dev only, must be explicitly enabled)
    Accept common alias 'header' -> 'headers'.
    """
    mode = os.environ.get("AUTH_MODE", "").strip().lower()
    if mode == "header":
        mode = "headers"
    return mode


def resolve_principal(request: Request):
    """
    Fail-closed:
      - If AUTH_MODE is 'jwt', require valid JWT claims.
      - If AUTH_MODE is 'headers', require ALLOW_INSECURE_HEADERS=true.
      - If AUTH_MODE is missing/unknown, allow headers only if explicitly enabled,
        otherwise 500.
    """
    mode = _auth_mode()

    if mode == "jwt":
        claims = get_jwt_claims_from_asgi_scope(request.scope)
        if not claims:
            raise HTTPException(status_code=401, detail="Missing/invalid JWT")
        return resolve_principal_from_jwt_claims(claims)

    if mode == "headers":
        if not _env_truthy("ALLOW_INSECURE_HEADERS"):
            raise HTTPException(
                status_code=500,
                detail="Server Misconfiguration: insecure headers blocked",
            )
        return resolve_principal_from_headers(request.headers)

    # If unset/unknown: ONLY allow headers if explicitly enabled (dev ergonomics)
    if _env_truthy("ALLOW_INSECURE_HEADERS"):
        return resolve_principal_from_headers(request.headers)

    logger.critical(
        "SECURITY_MISCONFIGURATION: AUTH_MODE must be 'jwt' (prod) "
        "or 'headers' with ALLOW_INSECURE_HEADERS=true (dev)."
    )
    raise HTTPException(status_code=500, detail="Server Authentication Misconfigured")


# -----------------------------------------------------------------------------
# Middleware: request_id + access log (owned by gateway)
# -----------------------------------------------------------------------------
@app.middleware("http")
async def request_context(request: Request, call_next):
    rid = _derive_request_id(request)

    # Correlate logs across the entire request lifecycle.
    token = request_id_ctx.set(rid)
    start = time.perf_counter()

    status_code = 500
    try:
        request.state.request_id = rid
        response = await call_next(request)
        status_code = getattr(response, "status_code", 500)

        # Always echo request id back
        response.headers["X-Request-Id"] = rid
        return response
    except Exception:
        # We still log request_complete below; re-raise to preserve FastAPI behavior.
        status_code = 500
        raise
    finally:
        duration_ms = int((time.perf_counter() - start) * 1000)

        # Minimal, safe, and consistent (no bodies, no headers, no queries).
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

    # 1) Scope calculation (auth-before-retrieval)
    allowed = {"public", "admin"} if p.role == "admin" else {"public"}
    scoped_docs = STORE.list_scoped(
        tenant_id=p.tenant_id, allowed_classifications=allowed
    )

    # 2) Ranking (simple deterministic lexical match)
    q = payload.query.strip().lower()
    tokens = [t for t in q.split() if t]

    def score(doc):
        text = (doc.title + " " + doc.body).lower()
        return sum(text.count(t) for t in tokens)

    ranked = sorted(scoped_docs, key=score, reverse=True)
    ranked = [d for d in ranked if score(d) > 0][:10]

    # 3) Projection & redaction (redact-before-slice)
    results = [
        QueryResult(
            doc_id=d.doc_id,
            title=d.title,
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

    return QueryResponse(request_id=request.state.request_id, results=results)


# -----------------------------------------------------------------------------
# Lambda handler
# -----------------------------------------------------------------------------
stage = os.environ.get("ENV", "dev").strip()
root_path = f"/{stage}" if stage else ""
handler = Mangum(app, api_gateway_base_path=root_path)
