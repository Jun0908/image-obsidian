from __future__ import annotations
import base64
from pathlib import Path

import anthropic

from storage import db


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def _image_to_b64(path: Path) -> tuple[str, str]:
    suffix_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    media_type = suffix_map.get(path.suffix.lower(), "image/jpeg")
    data = base64.standard_b64encode(path.read_bytes()).decode()
    return data, media_type


def narrate_connection(node_id_a: str, node_id_b: str) -> str:
    """
    2枚の画像を選択し、Claude に「なぜこの2枚はつながったのか」を問う。
    画像はローカルのみで完結（ユーザーがオプトインした場合のみ呼ぶ）。
    """
    node_a = db.get_node(node_id_a)
    node_b = db.get_node(node_id_b)

    if node_a is None or node_b is None:
        return "ノードが見つかりませんでした。"

    path_a = Path(node_a.file_path)
    path_b = Path(node_b.file_path)

    if not path_a.exists() or not path_b.exists():
        return "画像ファイルが見つかりませんでした。"

    data_a, mt_a = _image_to_b64(path_a)
    data_b, mt_b = _image_to_b64(path_b)

    prompt = (
        "以下の2枚の画像を見てください。\n"
        "あなたの役割は、これら2枚の画像が視覚的・感情的・概念的にどのように呼応しているかを、"
        "詩的かつ洞察力のある言葉で言語化することです。\n\n"
        "・共通する光や色の質感\n"
        "・構図や視線の方向性\n"
        "・喚起される感情や記憶のトーン\n"
        "・無意識が共鳴する何か\n\n"
        "200字以内で、日本語で答えてください。"
    )

    response = _client().messages.create(
        model="claude-opus-4-8",
        max_tokens=400,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": mt_a, "data": data_a}},
                    {"type": "image", "source": {"type": "base64", "media_type": mt_b, "data": data_b}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return response.content[0].text
