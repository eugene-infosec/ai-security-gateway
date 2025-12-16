from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

Classification = Literal["public", "admin"]


class IngestRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10_000)
    classification: Classification


class IngestResponse(BaseModel):
    doc_id: str
    request_id: str
