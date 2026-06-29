# image_obsidian — 実装計画

## コンセプト

PDFの思想「The Obsidian Gallery」を実装に落とし込む。  
Obsidianの知識グラフ構造を**画像**に応用した**私的視覚ネットワーク**システム。

画像1枚をノードとして扱い、AIが視覚的・感情的な類似性を自動検出してエッジを張る。  
整理するのではなく、**星座のように文脈が浮かび上がる**ことを目指す。

---

## 設計原則（PDFから導出）

| 原則 | 意味 | 実装上の制約 |
|---|---|---|
| **Save Before Naming** | 名前なしで画像を取り込む | 取り込み時にファイル名・タグは不要 |
| **Pre-verbal Intuition** | 言語化前の直感をそのまま保存 | 説明入力を強制しない |
| **Accumulation & Emergence** | 整理ではなく出現 | 自動クラスタリング、手動整理は後から |
| **Private First** | プライベート層は絶対 | 全データをローカル保存、外部送信なし（AI分析時のみオプトイン） |

---

## アーキテクチャ

```
image_obsidian/
├── core/
│   ├── vault.py          # Vault管理（Obsidian Vault相当）
│   ├── node.py           # 画像Nodeのデータ構造
│   ├── link.py           # ノード間リンク（自動 + 手動）
│   └── graph.py          # グラフ構造（networkx）
├── ai/
│   ├── embedder.py       # CLIP による画像ベクトル生成
│   ├── cluster.py        # 類似度クラスタリング（Phase 1）
│   └── narrator.py       # 「なぜ繋がったのか」AI言語化（Phase 2）
├── ui/
│   ├── graph_view/       # Force-directed ネットワークグラフ（D3.js）
│   ├── gallery_view/     # サムネイルギャラリー
│   └── dialogue_view/    # AI対話UI（Phase 2）
├── storage/
│   ├── vault/            # 画像ローカル保存（Private Layer）
│   └── metadata.db       # SQLite: ノード・エッジメタデータ
└── api/
    └── server.py         # FastAPI ローカルサーバー（localhost only）
```

---

## フェーズ別実装計画

### Phase 0 — インフラ（最初に作る）

**目標:** 画像を取り込んでDBに保存できる状態にする

- [ ] プロジェクト初期化（`pyproject.toml` or `requirements.txt`）
- [ ] SQLite スキーマ設計
  ```sql
  nodes: id, file_path, created_at, embedding (blob), tags (json), memo
  edges: id, source_id, target_id, similarity, edge_type (auto|manual), created_at
  clusters: id, name, node_ids (json), ai_description
  ```
- [ ] `vault.py`: Vault初期化、画像取り込み（名前不要、ハッシュでファイル名生成）
- [ ] `node.py`: Nodeデータクラス（id, path, embedding, tags, memo, created_at）
- [ ] FastAPI サーバー起動確認（localhost:8000）

---

### Phase 1 — Accumulation & Emergence

**目標:** 画像を投入するだけで、類似ノードが自動でつながるグラフが表示される

**バックエンド:**
- [ ] `embedder.py`: CLIP（`openai/clip-vit-base-patch32`）で画像→512次元ベクトル
- [ ] `cluster.py`: コサイン類似度でエッジ自動生成（閾値 > 0.75 でリンク）
- [ ] API エンドポイント
  - `POST /images/ingest` — 画像取り込み + 埋め込み生成 + 類似エッジ自動生成
  - `GET /graph` — ノード・エッジ一覧取得
  - `PATCH /nodes/{id}` — タグ・メモの後付け付与

**フロントエンド（Next.js + D3.js）:**
- [ ] ドラッグ&ドロップ取り込みUI（名前入力不要）
- [ ] Force-directed グラフビュー（D3.js `forceSimulation`）
  - ノード: 画像サムネイル
  - エッジ: 類似度の強さで太さを変える
  - 類似ノードが引き合って自然にクラスタを形成
- [ ] ノードクリック: 画像拡大 + タグ・メモ入力パネル

**MVP完成条件:** 複数枚の画像をドロップ → グラフに自動で星座が出現する

---

### Phase 2 — Dialogue with the Unconscious

**目標:** AIが「なぜこの2枚はつながったのか」を言語化する

- [ ] `narrator.py`: Claude API で選択ノード群の説明文生成
  - 入力: 2枚以上の画像URL + 類似度スコア
  - 出力: 「これらの画像が呼応する理由」の詩的・分析的テキスト
- [ ] クラスタ全体の「美意識プロファイル」生成
  - 「あなたが繰り返し惹きつけられているのは〇〇という感覚です」
- [ ] AI対話UI: ノードを2枚選択 → 「なぜ繋がったか」ボタン → 右パネルに言語化テキスト表示

**プライバシー注意:** 画像をAPIに送信することをユーザーがオプトインした場合のみ実行

---

### Phase 3 — Artwork as Node（将来スコープ）

PDFのArchitecture of Trust 3層構造を実装

- [ ] **Private Layer**: Phase 1・2がここに相当（ローカル記憶写真・個人画像）
- [ ] **Translation Layer**: Phase 2のAIナレーション（Confidential AI）
- [ ] **Public Layer**: 収蔵作品ノードの来歴証明との接続（Artist Room）

---

## 技術スタック

| レイヤー | 技術 | 理由 |
|---|---|---|
| 画像埋め込み | CLIP (`transformers` + `torch`) | オフライン実行可能、視覚的類似性に強い |
| バックエンド | Python 3.11 + FastAPI | 軽量、ローカル動作、非同期処理 |
| グラフ計算 | `networkx` + `numpy` | 類似度計算・クラスタリング |
| フロントエンド | Next.js 14 + TypeScript | React Server Components でサクサク |
| グラフUI | D3.js v7 (`forceSimulation`) | Obsidianのグラフビューと同等の表現 |
| AIナレーション | Claude API (`claude-opus-4-8`) | Phase 2の言語化品質 |
| ストレージ | SQLite（`sqlite3`）+ ローカルFS | プライベート絶対、サーバー不要 |

---

## 最初に着手するMVP（Phase 0 + Phase 1前半）

```
1. image_obsidian/ ディレクトリ作成
2. Python環境セットアップ（CLIP + FastAPI）
3. 画像取り込み → SQLite保存 → CLIP埋め込み生成
4. 類似度計算 → エッジ自動生成
5. GET /graph APIでノード・エッジJSON返却
6. Next.js + D3.js で最小グラフビュー表示
```

これで「画像を投入 → ネットワークが浮かび上がる」体験が完成する。

---

## ディレクトリ構造（初期作成分）

```
Product_629/
├── Plan.md                    ← このファイル
├── image_obsidian/
│   ├── backend/
│   │   ├── core/
│   │   ├── ai/
│   │   ├── storage/
│   │   └── api/server.py
│   └── frontend/
│       └── (Next.js プロジェクト)
└── pdf_pages/                 ← 参照資料
```
