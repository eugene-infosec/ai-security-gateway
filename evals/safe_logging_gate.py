import sys
import logging
from fastapi.testclient import TestClient
from app.main import app
from app.store import STORE

# --- SILENCE NOISE ---
# Only show WARNINGS or ERRORS. Hide INFO logs.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("app").setLevel(logging.WARNING)
# ---------------------

CANARY = "SECRET_SHOULD_NEVER_APPEAR"

class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.msgs = []
    def emit(self, record):
        self.msgs.append(record.getMessage())

def h(user="u", tenant="A", role="admin"):
    return {"X-User": user, "X-Tenant": tenant, "X-Role": role}

def main():
    STORE.clear()
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    handler = ListHandler()
    logger.addHandler(handler)
    logger.propagate = False 

    client = TestClient(app)

    # 1. Canary in body (must never appear in logs)
    r = client.post("/ingest", headers=h(role="admin"), json={
        "title": "Internal", "body": f"hello {CANARY} world", "classification": "internal",
    })
    assert r.status_code == 200

    # 2. Check logs
    leaked = []
    for msg in handler.msgs:
        if CANARY in msg:
            leaked.append("canary appeared in logs")
        try:
            obj = json.loads(msg)
            for bad in ["body", "raw_query", "authorization"]:
                if bad in obj:
                    leaked.append(f"unsafe log key: {bad}")
        except: pass

    logger.removeHandler(handler)
    if leaked:
        print("FAIL safe_logging_gate:", leaked)
        return 1

    print("PASS safe_logging_gate")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())