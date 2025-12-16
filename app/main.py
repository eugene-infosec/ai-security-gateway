from fastapi import FastAPI, Request
from mangum import Mangum
from app.middleware import CorrelationMiddleware

app = FastAPI(title="AI Security Gateway")

# Enforce observability middleware globally
app.add_middleware(CorrelationMiddleware)


@app.get("/health")
def health_check(request: Request):
    """
    Liveness probe.
    Returns request_id to prove middleware is active.
    """
    return {"ok": True, "request_id": request.state.request_id}


# Lambda Handler (for AWS)
handler = Mangum(app)
