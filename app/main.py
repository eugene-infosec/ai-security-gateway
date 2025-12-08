from __future__ import annotations

import time
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.logger import log_safe
from app.middleware.request_id import RequestIdMiddleware
# Updated imports
from app.auth import get_principal, Principal
from app.policy import is_allowed

app = FastAPI(title="AI Security Gateway")

app.add_middleware(RequestIdMiddleware)

@app.get("/health")
def health(request: Request):
    return {"ok": True, "request_id": getattr(request.state, "request_id", None)}

@app.get("/whoami")
def whoami(principal: Principal = Depends(get_principal)):
    """
    Proof Endpoint: Verifies that 'Authority Derivation' is working.
    Returns the server-derived identity, not just what was claimed.
    """
    return principal.model_dump()

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