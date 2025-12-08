from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.policy import Classification

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class IngestRequest(BaseModel):
    """
    Client-facing payload.
    NOTE: We explicitly define tenant_id so we can catch it and throw a
    specific security error (400 TENANT_FIELD_FORBIDDEN) if a client tries to set it.
    """
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10_000)

    # Optional; default handled server-side
    classification: Optional[str] = None

    # Anti-spoofing: The Trap
    tenant_id: Optional[str] = None


class StoredDoc(BaseModel):
    """
    Server/store model.
    tenant_id is derived from Principal (not request JSON).
    classification is validated + role-bounded.
    """
    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10_000)
    classification: Classification
    created_at: datetime