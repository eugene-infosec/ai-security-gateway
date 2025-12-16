import time
import uuid
import json
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.settings import settings

# Configure structured logging
logger = logging.getLogger("app")
logger.setLevel(settings.LOG_LEVEL)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))  # Raw JSON
logger.addHandler(handler)


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Generate Correlation ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 2. Start Timer
        start_time = time.time()

        # 3. Process Request
        response = await call_next(request)

        # 4. Calculate Latency
        process_time = (time.time() - start_time) * 1000

        # 5. Emit Structured Log (Safe Logging Contract)
        # INVARIANT: Never log body, query params, or auth headers here.
        log_event = {
            "event": "http_request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "latency_ms": round(process_time, 2),
        }
        logger.info(json.dumps(log_event))

        # 6. Return ID to client for debugging
        response.headers["X-Request-ID"] = request_id
        return response
