from __future__ import annotations

import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.logger import log_safe
from app.middleware.request_id import RequestIdMiddleware

app = FastAPI(title="AI Security Gateway")

# 1. Add Request ID first (so it exists for logging)
app.add_middleware(RequestIdMiddleware)

@app.get("/health")
def health(request: Request):
    return {"ok": True, "request_id": getattr(request.state, "request_id", None)}

# 2. Access Log Middleware (Manual implementation for control)
@app.middleware("http")
async def access_log(request: Request, call_next):
    start = time.perf_counter()
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        # Always run this, even if the app crashes
        latency_ms = int((time.perf_counter() - start) * 1000)
        status = getattr(response, "status_code", 500)
        
        log_safe(
            {
                "event": "http_request",
                "request_id": getattr(request.state, "request_id", None),
                "method": request.method,
                "path": request.url.path,
                "status": status,
                "latency_ms": latency_ms,
            }
        )

# 3. Global Exception Handler (Prevent stack traces in API responses)
@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    # Keep response generic; do not log request body or headers
    log_safe(
        {
            "event": "unhandled_exception",
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "status": 500,
            "latency_ms": 0,
            "error": "internal_error"
        }
    )
    return JSONResponse(status_code=500, content={"error": "internal_error"})