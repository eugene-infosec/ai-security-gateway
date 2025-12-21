import os
import uuid
import logging  # <--- ADDED THIS
from fastapi import FastAPI, Request, HTTPException
from mangum import Mangum
from app.json_logger import setup_logging

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

# Initialize the logger for this file
logger = logging.getLogger(__name__)  # <--- ADDED THIS

app = FastAPI(title="AI Security Gateway")


# If AUTH_MODE is not explicitly set, we crash. No guessing.
AUTH_MODE = os.environ.get("AUTH_MODE", "").lower()

if AUTH_MODE not in ("jwt", "headers"):
    # Allow headers ONLY if explicitly flagged (e.g. for local dev)
    # This prevents accidental deployment of header-auth to prod.
    if os.environ.get("ALLOW_INSECURE_HEADERS") == "true":
        AUTH_MODE = "headers"
    else:
        # We use a logger warning here, but practically we want to fail startup
        # or fail the first request.
        logger.critical(
            "SECURITY_MISCONFIGURATION: AUTH_MODE not set to 'jwt' and insecure headers not explicitly allowed."
        )
        # In Lambda, we can't easily "crash" the init process without cold start loops,
        # so we will enforce this in the resolve_principal function.


def resolve_principal(request: Request):
    # 2. ENFORCE CONFIGURATION
    if AUTH_MODE == "jwt":
        claims = get_jwt_claims_from_asgi_scope(request.scope)
        if not claims:
            raise HTTPException(status_code=401, detail="Missing/invalid JWT")
        return resolve_principal_from_jwt_claims(claims)

    elif AUTH_MODE == "headers":
        # Double check the explicit allow flag (defense in depth)
        if os.environ.get("ALLOW_INSECURE_HEADERS") != "true":
            raise HTTPException(
                status_code=500,
                detail="Server Misconfiguration: Insecure headers blocked",
            )
        return resolve_principal_from_headers(request.headers)

    else:
        # Fallback for undefined state
        raise HTTPException(
            status_code=500, detail="Server Authentication Misconfigured"
        )


# ... (Middleware & Health Check remain same) ...


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


@app.get("/health")
def health(request: Request):
    return {"ok": True, "request_id": request.state.request_id}


@app.get("/whoami")
def whoami(request: Request):
    p = resolve_principal(request)  # <--- CHANGED
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
    p = resolve_principal(request)  # <--- CHANGED

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

    # 1. Scope Calculation
    allowed = {"public", "admin"} if p.role == "admin" else {"public"}
    scoped_docs = STORE.list_scoped(
        tenant_id=p.tenant_id, allowed_classifications=allowed
    )

    # 2. Ranking (Simple Keyword Match)
    q = payload.query.strip().lower()
    tokens = [t for t in q.split() if t]

    def score(doc):
        text = (doc.title + " " + doc.body).lower()
        return sum(text.count(t) for t in tokens)

    ranked = sorted(scoped_docs, key=score, reverse=True)
    ranked = [d for d in ranked if score(d) > 0][:10]

    # 3. Projection & Redaction (Defense in Depth)
    results = [
        QueryResult(
            doc_id=d.doc_id,
            title=d.title,
            # SAFETY: Redact the snippet before it leaves the trust boundary
            snippet=redact_text(d.body[:160]),
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


# Lambda Handler

stage = os.environ.get("ENV", "dev")
root_path = f"/{stage}" if stage else ""
handler = Mangum(app, api_gateway_base_path=root_path)
