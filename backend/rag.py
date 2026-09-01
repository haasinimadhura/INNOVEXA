"""
INNOVEXA - rag.py
Local RAG pipeline: PDF -> extract -> chunk -> embed -> vector index -> retrieve.

Fixed issues:
  * Indexing new uploads no longer WIPES previously indexed documents.
    build_knowledge_base() now merges by default (incremental index).
  * Similarity scores are now consistent and human-readable (cosine 0..1) for
    both the FAISS path and the numpy fallback path - previously FAISS returned
    L2 distances (lower = better) while the fallback returned dot products
    (higher = better), so relevance ordering/labels were wrong.
  * chunk_count / status is read from the persisted index, so /kb-status is
    correct right after a restart instead of reporting 0 chunks.
  * Empty / image-only / unreadable PDFs report a clear per-document status.
"""

from __future__ import annotations

import json
import pickle
import re
from pathlib import Path
from typing import Dict, List, Optional

KB_DIR   = Path("data/manuals")
KB_INDEX = Path("data/kb_index.pkl")
KB_META  = Path("data/kb_meta.json")

KB_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 400
OVERLAP    = 80
MIN_SCORE  = 0.15          # drop clearly irrelevant chunks

_embedder = None
_chunks: List[Dict] = []
_matrix = None             # normalized float32 embedding matrix
_index = None              # faiss.IndexFlatIP when faiss is installed
_loaded = False


# ── Embeddings ────────────────────────────────────────────────────────────────
def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _embed(texts: List[str]):
    import numpy as np
    vecs = _get_embedder().encode(texts, show_progress_bar=False, batch_size=32)
    vecs = np.asarray(vecs, dtype="float32")
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms                      # cosine == dot product


# ── PDF extraction ────────────────────────────────────────────────────────────
def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
    pages: List[Dict] = []
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("[RAG] PyMuPDF not installed - run: pip install pymupdf")
        return pages
    try:
        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                text = re.sub(r"\s+", " ", page.get_text("text") or "").strip()
                if text:
                    pages.append({"page": page_num, "text": text})
    except Exception as exc:
        print(f"[RAG] PDF extraction error for {pdf_path}: {exc}")
    return pages


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> List[str]:
    words = text.split()
    if not words:
        return []
    step = max(1, chunk_size - overlap)
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), step)
            if words[i:i + chunk_size]]


# ── Persistence ───────────────────────────────────────────────────────────────
def _save():
    import numpy as np
    KB_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with KB_INDEX.open("wb") as fh:
        pickle.dump({"chunks": _chunks,
                     "matrix": np.asarray(_matrix, dtype="float32") if _matrix is not None else None,
                     "version": 2}, fh)


def _rebuild_ann():
    """Build the FAISS inner-product index from the stored matrix (optional)."""
    global _index
    _index = None
    if _matrix is None or len(_chunks) == 0:
        return
    try:
        import faiss
        idx = faiss.IndexFlatIP(int(_matrix.shape[1]))
        idx.add(_matrix)
        _index = idx
    except Exception:
        _index = None      # numpy fallback handles search


def _load_index() -> bool:
    """Load the persisted index. Tolerates the old v1 pickle format."""
    global _chunks, _matrix, _loaded
    if _loaded:
        return bool(_chunks)
    _loaded = True
    if not KB_INDEX.exists():
        return False
    try:
        import numpy as np
        with KB_INDEX.open("rb") as fh:
            data = pickle.load(fh)
        _chunks = data.get("chunks") or []
        matrix = data.get("matrix")
        if matrix is None:                                # legacy v1 pickle
            legacy = data.get("index")
            if isinstance(legacy, dict) and legacy.get("embeddings") is not None:
                matrix = legacy["embeddings"]
            elif _chunks:                                 # re-embed from chunks
                matrix = _embed([c["text"] for c in _chunks])
        if matrix is not None:
            matrix = np.asarray(matrix, dtype="float32")
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            matrix = matrix / norms
        _matrix = matrix
        _rebuild_ann()
        return bool(_chunks)
    except Exception as exc:
        # A stale / incompatible index (e.g. a v1 pickle holding a FAISS object
        # on a machine where faiss is not installed) used to leave RAG silently
        # dead. Self-heal by re-indexing the PDFs that are still on disk.
        print(f"[RAG] Index load error: {exc} — attempting automatic rebuild")
        _chunks, _matrix = [], None
        try:
            if any(KB_DIR.glob("*.pdf")):
                build_knowledge_base(pdf_paths=None)
                return bool(_chunks)
        except Exception as rebuild_exc:
            print(f"[RAG] Automatic rebuild failed: {rebuild_exc}")
        return False


# ── Build / update ────────────────────────────────────────────────────────────
def build_knowledge_base(pdf_paths: Optional[List[str]] = None,
                         replace: bool = False) -> Dict:
    """
    Index PDFs.
      pdf_paths=None -> index every PDF in data/manuals
      replace=False  -> MERGE with the existing index (default, incremental)
      replace=True   -> full rebuild
    """
    global _chunks, _matrix, _loaded
    import numpy as np

    full_scan = pdf_paths is None
    if full_scan:
        pdf_paths = [str(p) for p in sorted(KB_DIR.glob("*.pdf"))]
        replace = True

    pdf_paths = [str(p) for p in (pdf_paths or [])]
    if not pdf_paths:
        return {"status": "warning", "message": "No PDF documents found.",
                "doc_count": len(get_kb_metadata()), "chunk_count": len(_chunks)}

    if replace:
        _chunks, _matrix, _loaded = [], None, True
        existing_meta: List[Dict] = []
    else:
        _load_index()
        existing_meta = get_kb_metadata()

    known = {m["filename"] for m in existing_meta}
    new_chunks: List[Dict] = []
    doc_meta: List[Dict] = []

    for pdf_path in pdf_paths:
        doc_name = Path(pdf_path).name
        if doc_name in known and not replace:
            doc_meta.append({"filename": doc_name, "pages": 0, "chunks": 0,
                             "status": "already indexed"})
            continue
        if not Path(pdf_path).exists():
            doc_meta.append({"filename": doc_name, "pages": 0, "chunks": 0,
                             "status": "missing file"})
            continue

        pages = extract_text_from_pdf(pdf_path)
        count = 0
        for p in pages:
            for chunk in _chunk_text(p["text"]):
                new_chunks.append({"text": chunk, "document": doc_name, "page": p["page"]})
                count += 1
        doc_meta.append({
            "filename": doc_name,
            "pages": len(pages),
            "chunks": count,
            "status": "indexed" if count else "no extractable text (scanned/image PDF?)",
        })
        known.add(doc_name)

    if new_chunks:
        vecs = _embed([c["text"] for c in new_chunks])
        _chunks = (_chunks or []) + new_chunks
        _matrix = vecs if _matrix is None else np.vstack([_matrix, vecs])
        _rebuild_ann()
        _save()

    # Merge metadata (new entries win)
    merged = {m["filename"]: m for m in existing_meta}
    for m in doc_meta:
        if m["status"] == "already indexed" and m["filename"] in merged:
            continue
        merged[m["filename"]] = m
    meta_list = list(merged.values())
    with KB_META.open("w", encoding="utf-8") as fh:
        json.dump(meta_list, fh, indent=2)

    indexed_docs = [m for m in meta_list if m.get("chunks")]
    return {
        "status": "success" if new_chunks or indexed_docs else "warning",
        "message": ("Knowledge base updated." if new_chunks
                    else "No new text indexed - documents may already be indexed or contain no text."),
        "doc_count": len(indexed_docs),
        "chunk_count": len(_chunks),
        "new_chunks": len(new_chunks),
        "documents": meta_list,
    }


def rebuild_all() -> Dict:
    """Full rebuild from every PDF on disk."""
    return build_knowledge_base(pdf_paths=None)


# ── Search ────────────────────────────────────────────────────────────────────
def search_documents(query: str, top_k: int = 3, min_score: float = MIN_SCORE) -> List[Dict]:
    """Semantic search -> [{text, document, page, score(0..1)}] ranked best-first."""
    if not (query or "").strip():
        return []
    if not _load_index() or _matrix is None or not _chunks:
        return []

    import numpy as np
    q = _embed([query])
    k = int(min(max(1, top_k), len(_chunks)))

    if _index is not None:
        scores, idxs = _index.search(q, k)
        pairs = [(float(s), int(i)) for s, i in zip(scores[0], idxs[0]) if i != -1]
    else:
        sims = (_matrix @ q.T).ravel()
        order = np.argsort(-sims)[:k]
        pairs = [(float(sims[i]), int(i)) for i in order]

    results = []
    for score, idx in pairs:
        if idx < 0 or idx >= len(_chunks):
            continue
        if score < min_score:
            continue
        results.append({**_chunks[idx], "score": round(score, 4)})
    return results


# ── Metadata ──────────────────────────────────────────────────────────────────
def get_kb_metadata() -> List[Dict]:
    if KB_META.exists():
        try:
            with KB_META.open(encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, list) else []
        except Exception:
            return []
    return []


def get_kb_status() -> Dict:
    indexed = _load_index()
    meta = get_kb_metadata()
    return {
        "indexed": bool(indexed and _chunks),
        "doc_count": len([m for m in meta if m.get("chunks")]) or (len(meta) if indexed else 0),
        "chunk_count": len(_chunks),
        "backend": "faiss" if _index is not None else "numpy",
        "documents": meta,
    }
