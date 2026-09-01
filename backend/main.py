"""
INNOVEXA — main.py
FastAPI backend entry point for the Sovereign AI Workbench.
"""

import os
import sys
import uuid
import shutil
import logging
import platform
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("innovexa.backend")

# ── Ensure project root is in path ────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)   # all relative paths resolve from project root

# ── Local imports ──────────────────────────────────────────────────────────────
from backend      import llm
from backend.agent  import run_agent
from backend.rag    import build_knowledge_base, get_kb_status, search_documents, rebuild_all
from backend.vision import check_vision_status
from backend.tools  import (
    create_maintenance_task,
    load_audit_logs,
    load_maintenance_tasks,
    generate_report,
    save_audit_log,
)

# ── Config ─────────────────────────────────────────────────────────────────────
OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

UPLOAD_DIR  = Path("data")
IMAGE_DIR   = UPLOAD_DIR / "images"
MANUAL_DIR  = UPLOAD_DIR / "manuals"
REPORT_DIR  = UPLOAD_DIR / "reports"

for d in (IMAGE_DIR, MANUAL_DIR, REPORT_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "INNOVEXA — Sovereign AI Workbench",
    description = "On-premise agentic AI for industrial inspection & maintenance.",
    version     = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ────────────────────────────────────────────────────────────────────
def _ollama_ok() -> bool:
    """Cached, fast-fail Ollama reachability check (see backend/llm.py)."""
    return llm.is_online()


def _safe_filename(filename: str) -> str:
    """Strip path components and unsafe characters; never return an empty name."""
    name = Path(filename or "").name  # drop any directory / traversal components
    cleaned = "".join(c for c in name if c.isalnum() or c in "._- ").strip()
    return cleaned or f"file_{uuid.uuid4().hex[:8]}"


def _save_upload(upload: UploadFile, dest_dir: Path) -> Path:
    """
    Save an uploaded file to dest_dir, prefixing with a short unique id so
    that two uploads with the same original filename never overwrite
    each other (previously caused silent data loss / KB confusion).
    """
    fname = _safe_filename(upload.filename)
    unique_prefix = uuid.uuid4().hex[:8]
    dest = dest_dir / f"{unique_prefix}_{fname}"
    try:
        with dest.open("wb") as fh:
            shutil.copyfileobj(upload.file, fh)
    finally:
        upload.file.close()
    return dest


def _validate_upload(upload: Optional[UploadFile], allowed_ext: set, max_size_mb: int = 50) -> Optional[str]:
    """Return an error message string if the upload is invalid, else None."""
    if upload is None or not upload.filename:
        return None
    ext = Path(upload.filename).suffix.lower()
    if ext not in allowed_ext:
        return f"'{upload.filename}': unsupported file type '{ext}'. Allowed: {sorted(allowed_ext)}"
    return None


# ── Shared upload constraints ─────────────────────────────────────────────────
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ALLOWED_PDF_EXT   = {".pdf"}
MAX_UPLOAD_MB     = 50


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/health", tags=["System"])
def health_check():
    """
    System health — Ollama/LLM, vision, RAG, storage.
    Answers in well under a second even when Ollama is unreachable: the
    Ollama probe is cached and uses a short fast-fail timeout. Previously this
    endpoint could take ~9s, so the frontend's own timeout fired first and the
    UI wrongly reported the BACKEND as OFFLINE.
    """
    ai = llm.probe()
    kb = get_kb_status()
    online = bool(ai.get("running")) and bool(ai.get("text_model"))

    return {
        "status":    "ok",
        "service":   "INNOVEXA",
        "version":   "1.1.0",
        "timestamp": datetime.now().isoformat(),
        "python":    sys.version.split()[0],
        "os":        platform.system(),
        "components": {
            "local_llm": {
                "status": "online" if online else "offline",
                "model":  ai.get("text_model") or OLLAMA_MODEL,
                "url":    ai.get("url"),
                "reason": "" if online else ai.get("reason", ""),
            },
            "rag": {
                "status":      "ready" if kb["indexed"] else "empty",
                "docs":        kb["doc_count"],
                "chunks":      kb["chunk_count"],
                "vector_store": kb.get("backend", "numpy"),
            },
            "vision": {
                "status": "online" if ai.get("vision_available") else "offline",
                "model":  ai.get("vision_model"),
                "reason": "" if ai.get("vision_available") else ai.get("reason", ""),
            },
            "storage": {
                "status":  "ok",
                "reports": len(list(REPORT_DIR.glob("*.txt"))),
                "images":  len(list(IMAGE_DIR.glob("*"))),
                "manuals": len(list(MANUAL_DIR.glob("*.pdf"))),
            },
        },
        "installed_models": ai.get("models", []),
        "data_mode": "ON-PREMISE",
    }


@app.get("/models", tags=["System"])
def list_models():
    """Installed Ollama models plus the auto-resolved text/vision selection."""
    ai = llm.probe(force=True)
    return {
        "ollama_running":  ai.get("running"),
        "models":          ai.get("models", []),
        "text_model":      ai.get("text_model"),
        "vision_model":    ai.get("vision_model"),
        "reason":          ai.get("reason", ""),
    }


# ── File Upload ────────────────────────────────────────────────────────────────
@app.post("/upload", tags=["Files"])
async def upload_file(
    file: UploadFile = File(...),
    file_type: str   = Form("document"),   # "image" | "document"
):
    """Upload a single file (image or PDF) to local storage."""
    if not file.filename:
        raise HTTPException(400, "No filename provided.")

    ext = Path(file.filename).suffix.lower()

    if file_type == "image" and ext not in ALLOWED_IMAGE_EXT:
        raise HTTPException(400, f"Invalid image type: {ext}. Allowed: {sorted(ALLOWED_IMAGE_EXT)}")
    if file_type == "document" and ext not in ALLOWED_PDF_EXT:
        raise HTTPException(400, f"Invalid document type: {ext}. Allowed: {sorted(ALLOWED_PDF_EXT)}")

    dest_dir = IMAGE_DIR if file_type == "image" else MANUAL_DIR
    saved    = _save_upload(file, dest_dir)

    size_mb = saved.stat().st_size / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        saved.unlink(missing_ok=True)
        raise HTTPException(413, f"File exceeds {MAX_UPLOAD_MB} MB limit.")

    return {
        "status":    "success",
        "filename":  saved.name,
        "path":      str(saved),
        "size_mb":   round(size_mb, 2),
        "file_type": file_type,
    }


# ── Main Analysis ──────────────────────────────────────────────────────────────
@app.post("/analyze", tags=["Analysis"])
async def analyze(
    machine_id:  str            = Form("Unknown Machine"),
    query:       str            = Form("Analyze this machine and recommend maintenance."),
    image:       Optional[UploadFile] = File(None),
    report_pdf:  Optional[UploadFile] = File(None),
    manual_pdf:  Optional[UploadFile] = File(None),
):
    """
    Core analysis endpoint.
    Accepts optional image + PDF uploads, runs the full agent pipeline.
    """
    machine_id = (machine_id or "").strip() or "Unknown Machine"
    query      = (query or "").strip() or "Analyze this machine and recommend maintenance."

    # ── Validate uploads before touching disk ────────────────────────────────
    for upload, allowed, label in (
        (image,      ALLOWED_IMAGE_EXT, "image"),
        (report_pdf, ALLOWED_PDF_EXT,   "report_pdf"),
        (manual_pdf, ALLOWED_PDF_EXT,   "manual_pdf"),
    ):
        err = _validate_upload(upload, allowed)
        if err:
            raise HTTPException(400, f"Invalid {label} upload — {err}")

    image_path  = None
    report_path = None
    manual_path = None

    try:
        if image and image.filename:
            p = _save_upload(image, IMAGE_DIR)
            if p.stat().st_size > MAX_UPLOAD_MB * 1024 * 1024:
                p.unlink(missing_ok=True)
                raise HTTPException(413, f"Image exceeds {MAX_UPLOAD_MB} MB limit.")
            image_path = str(p)

        if report_pdf and report_pdf.filename:
            p = _save_upload(report_pdf, MANUAL_DIR)
            if p.stat().st_size > MAX_UPLOAD_MB * 1024 * 1024:
                p.unlink(missing_ok=True)
                raise HTTPException(413, f"Report PDF exceeds {MAX_UPLOAD_MB} MB limit.")
            report_path = str(p)

        if manual_pdf and manual_pdf.filename:
            p = _save_upload(manual_pdf, MANUAL_DIR)
            if p.stat().st_size > MAX_UPLOAD_MB * 1024 * 1024:
                p.unlink(missing_ok=True)
                raise HTTPException(413, f"Manual PDF exceeds {MAX_UPLOAD_MB} MB limit.")
            manual_path = str(p)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Upload handling failed")
        raise HTTPException(500, f"Failed to save uploaded file(s): {exc}")

    try:
        result = run_agent(
            machine_id  = machine_id,
            query       = query,
            image_path  = image_path,
            report_path = report_path,
            manual_path = manual_path,
        )
    except Exception as exc:
        logger.exception("Agent pipeline failed")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": f"Agent pipeline failed: {exc}",
                "machine_id": machine_id,
                "query": query,
            },
        )

    return JSONResponse(content=result)


# ── Build Knowledge Base ───────────────────────────────────────────────────────
@app.post("/build-kb", tags=["RAG"])
async def build_kb(
    files: list[UploadFile] = File(...),
):
    """Upload one or more PDFs and (re)build the FAISS knowledge base."""
    saved_paths = []
    try:
        for f in files:
            if not f.filename or Path(f.filename).suffix.lower() not in ALLOWED_PDF_EXT:
                raise HTTPException(400, f"Invalid document type for '{f.filename}'. Only PDF is allowed.")
            p = _save_upload(f, MANUAL_DIR)
            saved_paths.append(str(p))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to save KB uploads")
        raise HTTPException(500, f"Failed to save uploaded file(s): {exc}")

    try:
        result = build_knowledge_base(pdf_paths=saved_paths)
    except Exception as exc:
        logger.exception("Knowledge base build failed")
        raise HTTPException(500, f"Failed to build knowledge base: {exc}")

    return result


@app.get("/kb-status", tags=["RAG"])
def kb_status():
    return get_kb_status()


@app.post("/rebuild-kb", tags=["RAG"])
def rebuild_kb():
    """Full re-index of every PDF already in data/manuals."""
    try:
        return rebuild_all()
    except Exception as exc:
        logger.exception("KB rebuild failed")
        raise HTTPException(500, f"Failed to rebuild knowledge base: {exc}")


@app.get("/search", tags=["RAG"])
def kb_search(q: str, top_k: int = 5):
    """Direct semantic search over the knowledge base (used by the UI)."""
    if not q.strip():
        raise HTTPException(400, "Query 'q' must not be empty.")
    try:
        return {"query": q, "results": search_documents(q, top_k=top_k)}
    except Exception as exc:
        logger.exception("KB search failed")
        raise HTTPException(500, f"Search failed: {exc}")


# ── Report Generation ──────────────────────────────────────────────────────────
@app.post("/generate-report", tags=["Reports"])
async def api_generate_report(
    machine_id:          str = Form(...),
    visual_observations: str = Form(""),
    possible_issue:      str = Form(""),
    risk_level:          str = Form("MEDIUM"),
    recommendation:      str = Form(""),
    audit_id:            str = Form("N/A"),
):
    result = generate_report(
        machine_id          = machine_id,
        visual_observations = visual_observations,
        possible_issue      = possible_issue,
        risk_level          = risk_level,
        rag_evidence        = [],
        recommendation      = recommendation,
        uploaded_files      = [],
        audit_id            = audit_id,
    )
    return result


@app.get("/reports", tags=["Reports"])
def list_reports():
    """List all generated reports."""
    reports = []
    for f in sorted(REPORT_DIR.glob("*.txt"), reverse=True):
        stat = f.stat()
        reports.append({
            "filename": f.name,
            "size_kb":  round(stat.st_size / 1024, 1),
            "created":  datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "path":     str(f),
        })
    return {"reports": reports}


@app.get("/reports/{filename}", tags=["Reports"])
def get_report(filename: str):
    path = REPORT_DIR / _safe_filename(filename)
    if not path.exists():
        raise HTTPException(404, "Report not found.")
    return FileResponse(path, media_type="text/plain", filename=filename)


# ── Maintenance Task ───────────────────────────────────────────────────────────
@app.post("/maintenance-task", tags=["Automation"])
async def api_maintenance_task(
    machine_id:     str = Form(...),
    issue:          str = Form("Potential component issue"),
    priority:       str = Form("MEDIUM"),
    recommendation: str = Form("Perform inspection per SOP."),
):
    result = create_maintenance_task(
        machine_id     = machine_id,
        issue          = issue,
        priority       = priority,
        recommendation = recommendation,
    )
    return result


@app.get("/maintenance-tasks", tags=["Automation"])
def list_tasks():
    return {"tasks": load_maintenance_tasks()}


# ── Audit Logs ─────────────────────────────────────────────────────────────────
@app.get("/audit-logs", tags=["Audit"])
def get_audit_logs(limit: int = 50):
    logs = load_audit_logs()[:limit]
    return {"audit_logs": logs, "total": len(logs)}


# ── Entry point (dev convenience) ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
