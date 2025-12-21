import os
import boto3

# Removed unused imports (List, Optional)
from app.models import Document  # Assuming you have a Document model


class InMemoryStore:
    def __init__(self):
        self.db = {}  # {doc_id: Document}

    def put(self, tenant_id, classification, title, body):
        import uuid

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

    # --- ADD THIS METHOD ---
    def clear(self):
        self.db = {}


class DynamoDBStore:
    def __init__(self, table_name):
        self.table = boto3.resource("dynamodb").Table(table_name)

    def put(self, tenant_id, classification, title, body):
        import uuid

        doc_id = str(uuid.uuid4())
        # PK = TENANT#<tenant_id>
        # SK = CLASS#<classification>#DOC#<doc_id>
        # This allows efficient querying by scope
        item = {
            "pk": f"TENANT#{tenant_id}",
            "sk": f"CLASS#{classification}#DOC#{doc_id}",
            "doc_id": doc_id,
            "tenant_id": tenant_id,
            "classification": classification,
            "title": title,
            "body": body,
        }
        self.table.put_item(Item=item)
        return Document(**item)

    def list_scoped(self, tenant_id, allowed_classifications):
        results = []
        for cls in allowed_classifications:
            # Efficient Query: Get everything for this Tenant + Classification
            resp = self.table.query(
                KeyConditionExpression="pk = :pk AND begins_with(sk, :sk)",
                ExpressionAttributeValues={
                    ":pk": f"TENANT#{tenant_id}",
                    ":sk": f"CLASS#{cls}",
                },
            )
            for item in resp.get("Items", []):
                results.append(Document(**item))
        return results


# Factory Logic
TABLE_NAME = os.environ.get("TABLE_NAME")

if TABLE_NAME:
    STORE = DynamoDBStore(TABLE_NAME)
else:
    STORE = InMemoryStore()
