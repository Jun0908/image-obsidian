from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json


@dataclass
class Node:
    id: str
    file_path: str
    created_at: datetime
    tags: list[str] = field(default_factory=list)
    memo: str = ""
    embedding: Optional[list[float]] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags,
            "memo": self.memo,
            "has_embedding": self.embedding is not None,
        }


@dataclass
class Edge:
    id: str
    source_id: str
    target_id: str
    similarity: float
    edge_type: str  # "auto" | "manual"
    created_at: datetime

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source_id,
            "target": self.target_id,
            "similarity": self.similarity,
            "edge_type": self.edge_type,
        }
