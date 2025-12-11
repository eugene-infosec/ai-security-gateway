import os
import boto3
from boto3.dynamodb.conditions import Key
from typing import Dict, List, Optional
from app.models import StoredDoc

# Interface (Implicit)
class InMemoryStore:
    def __init__(self):
        # Structural Isolation: Key is tenant_id, Value is {doc_id: doc}
        self.data: Dict[str, Dict[str, StoredDoc]] = {}

    def put_doc(self, doc: StoredDoc) -> None:
        if doc.tenant_id not in self.data:
            self.data[doc.tenant_id] = {}
        self.data[doc.tenant_id][doc.doc_id] = doc

    def list_docs(self, tenant_id: str) -> List[StoredDoc]:
        # Structural isolation: Only look in this tenant's dict
        tenant_store = self.data.get(tenant_id, {})
        return list(tenant_store.values())

    def get_doc(self, tenant_id: str, doc_id: str):
        # Missing helper that tests rely on
        return self.data.get(tenant_id, {}).get(doc_id)

    def clear(self) -> None:
        # Used by tests to reset state
        self.data.clear()

class DynamoDBStore:
    def __init__(self, table_name: str):
        self.table = boto3.resource("dynamodb").Table(table_name)

    def clear(self): pass # No-op in cloud

    def put_doc(self, doc: StoredDoc) -> None:
        item = doc.model_dump(mode="json")
        item["PK"] = f"TENANT#{doc.tenant_id}"
        item["SK"] = f"DOC#{doc.doc_id}"
        self.table.put_item(Item=item)

    def list_docs(self, tenant_id: str) -> List[StoredDoc]:
        resp = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"TENANT#{tenant_id}")
        )
        # CLEAN FIX: Parse without mutating original items
        clean = []
        for item in resp.get("Items", []):
            item = dict(item)
            item.pop("PK", None)
            item.pop("SK", None)
            clean.append(StoredDoc(**item))
        return clean

    def get_doc(self, tenant_id: str, doc_id: str) -> Optional[StoredDoc]:
        resp = self.table.get_item(
            Key={"PK": f"TENANT#{tenant_id}", "SK": f"DOC#{doc_id}"}
        )
        item = resp.get("Item")
        if not item: return None
        
        item = dict(item)
        item.pop("PK", None)
        item.pop("SK", None)
        return StoredDoc(**item)

# FACTORY
TABLE_NAME = os.getenv("TABLE_NAME")
STORE = DynamoDBStore(TABLE_NAME) if TABLE_NAME else InMemoryStore()