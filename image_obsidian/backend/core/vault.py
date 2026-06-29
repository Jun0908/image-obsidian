from __future__ import annotations
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

from core.node import Node
from storage import db

VAULT_DIR = Path(__file__).parent.parent / "storage" / "vault"


def _ensure_vault() -> None:
    VAULT_DIR.mkdir(parents=True, exist_ok=True)


def ingest_image(src_path: Path) -> Node:
    """
    画像をVaultにコピーしてNodeを作成する。
    名前は付けない（SHA256ハッシュをIDとして使用）。
    """
    _ensure_vault()

    with open(src_path, "rb") as f:
        content = f.read()

    node_id = hashlib.sha256(content).hexdigest()[:16]
    suffix = src_path.suffix.lower()
    dest_path = VAULT_DIR / f"{node_id}{suffix}"

    if not dest_path.exists():
        shutil.copy2(src_path, dest_path)

    node = Node(
        id=node_id,
        file_path=str(dest_path),
        created_at=datetime.now(timezone.utc),
    )
    db.insert_node(node)
    return node


def ingest_bytes(data: bytes, suffix: str) -> Node:
    """アップロードされたバイト列から画像を取り込む。"""
    _ensure_vault()

    node_id = hashlib.sha256(data).hexdigest()[:16]
    dest_path = VAULT_DIR / f"{node_id}{suffix}"

    if not dest_path.exists():
        dest_path.write_bytes(data)

    node = Node(
        id=node_id,
        file_path=str(dest_path),
        created_at=datetime.now(timezone.utc),
    )
    db.insert_node(node)
    return node


def get_vault_image_path(node_id: str) -> Path | None:
    node = db.get_node(node_id)
    if node is None:
        return None
    path = Path(node.file_path)
    return path if path.exists() else None
