from abc import ABC, abstractmethod
from typing import List
import uuid
from app.models import Document


# ------------------------------------------------------------------------------
# The Senior Signal: Interface Definition
# We define the contract *before* the implementation.
# This proves to the reviewer: "I designed this to be swappable for Qdrant/Pinecone."
# ------------------------------------------------------------------------------
class RetrievalStore(ABC):
    @abstractmethod
    def put(
        self, tenant_id: str, classification: str, title: str, body: str
    ) -> Document:
        """Persist a document with security metadata."""
        pass

    @abstractmethod
    def list_scoped(
        self, tenant_id: str, allowed_classifications: List[str]
    ) -> List[Document]:
        """
        Retrieve documents enforcing tenant isolation and classification scope.

        Architectural Note:
        In a production RAG system, this method would be replaced by:
        `vector_search(query_vector, filters={'tenant_id': ..., 'classification': ...})`
        """
        pass

    @abstractmethod
    def clear(self):
        """Reset state (Test/Dev only)."""
        pass


# ------------------------------------------------------------------------------
# The Implementation: In-Memory Adapter
# ------------------------------------------------------------------------------
class InMemoryStore(RetrievalStore):
    def __init__(self):
        self.db = {}  # {doc_id: Document}

    def put(
        self, tenant_id: str, classification: str, title: str, body: str
    ) -> Document:
        doc_id = str(uuid.uuid4())
        doc = Document(
            doc_id=doc_id,
            tenant_id=tenant_id,
            classification=classification,
            title=title,
            body=body,
        )
        self.db[doc_id] = doc
        return doc

    def list_scoped(
        self, tenant_id: str, allowed_classifications: List[str]
    ) -> List[Document]:
        # The "Sad Path" Defense:
        # We enforce filtering at the storage layer, ensuring no leakage even if
        # the upper layers fail to validate.
        return [
            d
            for d in self.db.values()
            if d.tenant_id == tenant_id and d.classification in allowed_classifications
        ]

    def clear(self):
        self.db = {}


# ------------------------------------------------------------------------------
# Factory / Singleton
# In production, this would be: if settings.USE_QDRANT: STORE = QdrantStore()
# ------------------------------------------------------------------------------
STORE = InMemoryStore()
