from __future__ import annotations
import uuid
from datetime import datetime, timezone

import numpy as np

from core.node import Node, Edge
from storage import db

SIMILARITY_THRESHOLD = 0.75


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-8))


def rebuild_edges_for_node(new_node: Node) -> list[Edge]:
    """
    新しいノードと既存全ノードの類似度を計算し、
    閾値を超えたペアに自動エッジを張る。
    """
    if new_node.embedding is None:
        return []

    all_nodes = db.get_all_nodes(include_embedding=True)
    new_edges: list[Edge] = []

    for existing in all_nodes:
        if existing.id == new_node.id:
            continue
        if existing.embedding is None:
            continue

        sim = cosine_similarity(new_node.embedding, existing.embedding)
        if sim >= SIMILARITY_THRESHOLD:
            edge = Edge(
                id=str(uuid.uuid4()),
                source_id=new_node.id,
                target_id=existing.id,
                similarity=round(sim, 4),
                edge_type="auto",
                created_at=datetime.now(timezone.utc),
            )
            db.insert_edge(edge)
            new_edges.append(edge)

    return new_edges


def get_graph_data() -> dict:
    """D3.js が受け取れる nodes / links 形式でグラフデータを返す。"""
    nodes = db.get_all_nodes()
    edges = db.get_all_edges()
    return {
        "nodes": [n.to_dict() for n in nodes],
        "links": [e.to_dict() for e in edges],
    }
