import uuid
from app.models import Document


class InMemoryStore:
    def __init__(self):
        self.db = {}  # {doc_id: Document}

    def put(self, tenant_id, classification, title, body):
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

    def list_scoped(self, tenant_id, allowed_classifications):
        return [
            d
            for d in self.db.values()
            if d.tenant_id == tenant_id and d.classification in allowed_classifications
        ]

    def clear(self):
        self.db = {}


# Factory Logic: Simplified to use Memory for the Demo
# This ensures reproducibility and eliminates the need for AWS credentials locally.
STORE = InMemoryStore()
