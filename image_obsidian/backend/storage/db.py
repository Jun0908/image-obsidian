from __future__ import annotations
import sqlite3
import json
import struct
from pathlib import Path
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

from core.node import Node, Edge

DB_PATH = Path(__file__).parent / "vault.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_conn():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS nodes (
                id          TEXT PRIMARY KEY,
                file_path   TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                tags        TEXT NOT NULL DEFAULT '[]',
                memo        TEXT NOT NULL DEFAULT '',
                embedding   BLOB
            );

            CREATE TABLE IF NOT EXISTS edges (
                id          TEXT PRIMARY KEY,
                source_id   TEXT NOT NULL,
                target_id   TEXT NOT NULL,
                similarity  REAL NOT NULL,
                edge_type   TEXT NOT NULL DEFAULT 'auto',
                created_at  TEXT NOT NULL,
                FOREIGN KEY (source_id) REFERENCES nodes(id),
                FOREIGN KEY (target_id) REFERENCES nodes(id)
            );
        """)


def _embedding_to_blob(embedding: list[float]) -> bytes:
    return struct.pack(f"{len(embedding)}f", *embedding)


def _blob_to_embedding(blob: bytes) -> list[float]:
    count = len(blob) // 4
    return list(struct.unpack(f"{count}f", blob))


def insert_node(node: Node) -> None:
    blob = _embedding_to_blob(node.embedding) if node.embedding else None
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO nodes (id, file_path, created_at, tags, memo, embedding) VALUES (?,?,?,?,?,?)",
            (node.id, node.file_path, node.created_at.isoformat(), json.dumps(node.tags), node.memo, blob),
        )


def update_node_meta(node_id: str, tags: list[str], memo: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE nodes SET tags=?, memo=? WHERE id=?",
            (json.dumps(tags), memo, node_id),
        )


def update_node_embedding(node_id: str, embedding: list[float]) -> None:
    blob = _embedding_to_blob(embedding)
    with get_conn() as conn:
        conn.execute("UPDATE nodes SET embedding=? WHERE id=?", (blob, node_id))


def get_all_nodes(include_embedding: bool = False) -> list[Node]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM nodes ORDER BY created_at DESC").fetchall()
    nodes = []
    for row in rows:
        emb = _blob_to_embedding(row["embedding"]) if (include_embedding and row["embedding"]) else None
        nodes.append(Node(
            id=row["id"],
            file_path=row["file_path"],
            created_at=datetime.fromisoformat(row["created_at"]),
            tags=json.loads(row["tags"]),
            memo=row["memo"],
            embedding=emb,
        ))
    return nodes


def get_node(node_id: str, include_embedding: bool = False) -> Optional[Node]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM nodes WHERE id=?", (node_id,)).fetchone()
    if not row:
        return None
    emb = _blob_to_embedding(row["embedding"]) if (include_embedding and row["embedding"]) else None
    return Node(
        id=row["id"],
        file_path=row["file_path"],
        created_at=datetime.fromisoformat(row["created_at"]),
        tags=json.loads(row["tags"]),
        memo=row["memo"],
        embedding=emb,
    )


def insert_edge(edge: Edge) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO edges (id, source_id, target_id, similarity, edge_type, created_at) VALUES (?,?,?,?,?,?)",
            (edge.id, edge.source_id, edge.target_id, edge.similarity, edge.edge_type, edge.created_at.isoformat()),
        )


def delete_edges_for_node(node_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM edges WHERE source_id=? OR target_id=?", (node_id, node_id))


def get_all_edges() -> list[Edge]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM edges").fetchall()
    return [
        Edge(
            id=row["id"],
            source_id=row["source_id"],
            target_id=row["target_id"],
            similarity=row["similarity"],
            edge_type=row["edge_type"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]
