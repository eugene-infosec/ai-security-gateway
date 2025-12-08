from __future__ import annotations

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-Id"

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Trust incoming ID (for distributed tracing) or generate new one
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming or str(uuid.uuid4())
        
        # 2. Attach to state for logging
        request.state.request_id = request_id

        # 3. Process
        response: Response = await call_next(request)
        
        # 4. Return to client
        response.headers[REQUEST_ID_HEADER] = request_id
        return response