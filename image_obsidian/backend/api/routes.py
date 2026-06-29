from __future__ import annotations
import os
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.vault import ingest_bytes, get_vault_image_path
from ai.embedder import embed_image
from ai.cluster import rebuild_edges_for_node, get_graph_data
from ai.narrator import narrate_connection
from storage import db

router = APIRouter()

ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


# ── 画像取り込み ──────────────────────────────────────────────
@router.post("/images/ingest")
async def ingest_image(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    data = await file.read()
    node = ingest_bytes(data, suffix)

    # CLIP 埋め込み生成 → エッジ自動生成
    image_path = Path(node.file_path)
    embedding = embed_image(image_path)
    node.embedding = embedding
    db.update_node_embedding(node.id, embedding)
    new_edges = rebuild_edges_for_node(node)

    return {
        "node": node.to_dict(),
        "new_edges": len(new_edges),
    }


# ── グラフデータ取得 ──────────────────────────────────────────
@router.get("/graph")
def graph():
    return get_graph_data()


# ── ノードメタ更新 ────────────────────────────────────────────
class NodeMeta(BaseModel):
    tags: list[str] = []
    memo: str = ""


@router.patch("/nodes/{node_id}")
def update_node(node_id: str, meta: NodeMeta):
    node = db.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    db.update_node_meta(node_id, meta.tags, meta.memo)
    return {"ok": True}


# ── 画像ファイル配信 ──────────────────────────────────────────
@router.get("/images/{node_id}")
def serve_image(node_id: str):
    path = get_vault_image_path(node_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(str(path))


# ── Phase 2: AI ナレーション ──────────────────────────────────
class NarrateRequest(BaseModel):
    node_id_a: str
    node_id_b: str


@router.post("/narrate")
def narrate(req: NarrateRequest):
    text = narrate_connection(req.node_id_a, req.node_id_b)
    return {"text": text}
