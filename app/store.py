from __future__ import annotations

from typing import Dict, List, Optional

from app.models import StoredDoc

class InMemoryStore:
    """
    Tenant-scoped storage.
    Structure: tenant_id -> doc_id -> StoredDoc

    Intentionally NO list_all_docs() to keep the API tenant-safe by design.
    """
    def __init__(self) -> None:
        self._docs: Dict[str, Dict[str, StoredDoc]] = {}

    def clear(self) -> None:
        self._docs.clear()

    def put_doc(self, doc: StoredDoc) -> None:
        self._docs.setdefault(doc.tenant_id, {})[doc.doc_id] = doc

    def get_doc(self, tenant_id: str, doc_id: str) -> Optional[StoredDoc]:
        return self._docs.get(tenant_id, {}).get(doc_id)

    def list_docs(self, tenant_id: str) -> List[StoredDoc]:
        return list(self._docs.get(tenant_id, {}).values())

STORE = InMemoryStore()