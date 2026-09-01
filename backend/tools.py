"""
INNOVEXA — tools.py
Safe local automation tools for industrial AI workbench.
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPORTS_DIR = Path("data/reports")
AUDIT_FILE  = Path("data/audit_log.jsonl")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

# ── In-memory maintenance history (demo) ──────────────────────────────────────
_MAINTENANCE_HISTORY = [
    {"date": "2024-11-15", "machine": "Industrial Pump P-102", "action": "Bearing lubrication", "technician": "T. Kumar", "status": "Completed"},
    {"date": "2024-09-03", "machine": "Industrial Pump P-102", "action": "Seal inspection",    "technician": "R. Sharma", "status": "Completed"},
    {"date": "2024-06-20", "machine": "Industrial Pump P-102", "action": "Impeller check",    "technician": "T. Kumar", "status": "Completed"},
]

# ── Tool: search_knowledge_base ───────────────────────────────────────────────
def search_knowledge_base(query: str, top_k: int = 3) -> dict:
    """Delegate to rag.py; returns chunks + metadata."""
    try:
        from backend.rag import search_documents
        results = search_documents(query, top_k=top_k)
        return {"status": "success", "results": results, "source": "rag"}
    except Exception as exc:
        return {"status": "error", "results": [], "error": str(exc)}


# ── Tool: analyze_image ───────────────────────────────────────────────────────
def analyze_image(image_path: str, query: str = "") -> dict:
    """Delegate to vision.py."""
    try:
        from backend.vision import analyze_image as vision_analyze
        return vision_analyze(image_path, query)
    except Exception as exc:
        return {
            "status": "error",
            "observations": "Vision module unavailable.",
            "possible_issues": "Unknown",
            "risk_level": "UNKNOWN",
            "confidence": "N/A",
            "error": str(exc),
            "demo_mode": True,
        }


# ── Tool: get_maintenance_history ─────────────────────────────────────────────
def get_maintenance_history(machine_id: str = "") -> dict:
    """Return local maintenance history records."""
    if machine_id:
        records = [r for r in _MAINTENANCE_HISTORY
                   if machine_id.lower() in r["machine"].lower()]
    else:
        records = _MAINTENANCE_HISTORY
    return {"status": "success", "machine_id": machine_id, "history": records}


# ── Tool: generate_report ─────────────────────────────────────────────────────
def _safe_slug(text: str, fallback: str = "Machine") -> str:
    """Turn arbitrary text into a filesystem-safe slug (no path separators)."""
    text = (text or "").strip().replace(" ", "_")
    slug = "".join(c for c in text if c.isalnum() or c in "._-")
    return slug or fallback


def generate_report(
    machine_id: str,
    visual_observations: str,
    possible_issue: str,
    risk_level: str,
    rag_evidence: list,
    recommendation: str,
    uploaded_files: list,
    audit_id: str,
    model_used: str = "local-ollama",
) -> dict:
    """Generate and save a structured industrial maintenance report."""
    report_id   = str(uuid.uuid4())[:8].upper()
    timestamp   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str    = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename    = f"INNOVEXA_Report_{_safe_slug(machine_id)}_{date_str}.txt"
    report_path = REPORTS_DIR / filename

    evidence_block = ""
    for i, ev in enumerate(rag_evidence, 1):
        evidence_block += (
            f"\n  [{i}] Document : {ev.get('document', 'N/A')}\n"
            f"       Page     : {ev.get('page', 'N/A')}\n"
            f"       Excerpt  : {ev.get('text', '')[:300]}\n"
        )

    report_text = f"""
================================================================================
                       INNOVEXA INDUSTRIAL AI REPORT
================================================================================

Report ID   : {report_id}
Machine ID  : {machine_id}
Date        : {timestamp}
Audit ID    : {audit_id}
Model Used  : {model_used}

Input Files
-----------
{chr(10).join(f'  • {f}' for f in uploaded_files) if uploaded_files else '  (none)'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VISUAL OBSERVATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{visual_observations}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POSSIBLE ISSUE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{possible_issue}

RISK LEVEL : {risk_level}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RELEVANT EVIDENCE (RAG)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{evidence_block if evidence_block else '  No RAG evidence available.'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDED ACTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{recommendation}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AI ASSISTANCE DISCLAIMER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This report is AI-generated assistance only. Visual observations indicate
POSSIBLE issues and require further physical inspection. Final industrial
maintenance decisions MUST be verified and approved by a qualified engineer.

================================================================================
                       END OF INNOVEXA REPORT
================================================================================
"""

    report_path.write_text(report_text, encoding="utf-8")

    return {
        "status": "success",
        "report_id": report_id,
        "filename": filename,
        "path": str(report_path),
        "timestamp": timestamp,
        "machine_id": machine_id,
    }


# ── Tool: create_maintenance_task ─────────────────────────────────────────────
def create_maintenance_task(
    machine_id: str,
    issue: str,
    priority: str,
    recommendation: str,
) -> dict:
    """Create a simulated (local-only) maintenance task record."""
    task_id   = "TASK-" + str(uuid.uuid4())[:6].upper()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    task = {
        "task_id": task_id,
        "machine_id": machine_id,
        "issue": issue,
        "priority": priority,
        "recommendation": recommendation,
        "created_time": timestamp,
        "status": "OPEN",
        "assigned_to": "Maintenance Team",
        "estimated_completion": "Within 24–48 hours (as per SOP)",
        "note": "SIMULATED — Not connected to any real industrial control system.",
    }

    # Persist tasks alongside audit log
    task_file = Path("data/maintenance_tasks.jsonl")
    with task_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(task) + "\n")

    return {"status": "success", "task": task}


# ── Tool: save_audit_log ──────────────────────────────────────────────────────
def save_audit_log(
    user_query: str,
    uploaded_files: list,
    tools_used: list,
    model_used: str,
    result_summary: str,
    machine_id: str = "",
    status: str = "success",
) -> dict:
    """Append one audit record to the local JSONL audit log."""
    audit_id  = "AUD-" + str(uuid.uuid4())[:8].upper()
    timestamp = datetime.now().isoformat()

    record = {
        "audit_id": audit_id,
        "timestamp": timestamp,
        "machine_id": machine_id,
        "user_query": user_query,
        "uploaded_files": uploaded_files,
        "tools_used": tools_used,
        "model_used": model_used,
        "result_summary": result_summary,
        "status": status,
    }

    with AUDIT_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")

    return {"status": "success", "audit_id": audit_id, "timestamp": timestamp}


# ── Helper: load audit logs ───────────────────────────────────────────────────
def load_audit_logs() -> list:
    if not AUDIT_FILE.exists():
        return []
    logs = []
    with AUDIT_FILE.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return list(reversed(logs))


# ── Helper: load maintenance tasks ───────────────────────────────────────────
def load_maintenance_tasks() -> list:
    task_file = Path("data/maintenance_tasks.jsonl")
    if not task_file.exists():
        return []
    tasks = []
    with task_file.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    tasks.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return list(reversed(tasks))
