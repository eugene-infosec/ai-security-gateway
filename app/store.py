from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import List, Set
import uuid


@dataclass(frozen=True)
class Document:
    doc_id: str
    tenant_id: str
    classification: str  # "public" | "admin"
    title: str
    body: str


class InMemoryStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._docs: list[Document] = []

    def clear(self) -> None:
        """Reset store for deterministic testing."""
        with self._lock:
            self._docs = []

    def put(
        self, *, tenant_id: str, classification: str, title: str, body: str
    ) -> Document:
        doc = Document(
            doc_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            classification=classification,
            title=title,
            body=body,
        )
        with self._lock:
            self._docs.append(doc)
        return doc

    def list_scoped(
        self, *, tenant_id: str, allowed_classifications: Set[str]
    ) -> List[Document]:
        """
        Structural Isolation:
        We never return other-tenant docs from this function.
        We never return forbidden classifications.
        """
        with self._lock:
            return [
                d
                for d in self._docs
                if d.tenant_id == tenant_id
                and d.classification in allowed_classifications
            ]

    def get(self, tenant_id: str, doc_id: str) -> Document | None:
        with self._lock:
            for d in self._docs:
                if d.tenant_id == tenant_id and d.doc_id == doc_id:
                    return d
        return None


STORE = InMemoryStore()
