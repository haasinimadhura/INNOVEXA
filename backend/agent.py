"""
INNOVEXA — agent.py
Agentic AI workflow: sense → retrieve → reason → act → record.
"""

import os
import json
import requests
from pathlib import Path
from typing import Optional

from backend import llm

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL  = os.getenv("OLLAMA_MODEL", "mistral")

from backend.tools import (
    analyze_image,
    search_knowledge_base,
    get_maintenance_history,
    generate_report,
    create_maintenance_task,
    save_audit_log,
)


# ── LLM call ──────────────────────────────────────────────────────────────────
def _call_llm(prompt: str, system: str = ""):
    """
    Call the local LLM through the shared client.
    Returns (text, error). The error is surfaced to the UI instead of being
    swallowed, so 'why am I in DEMO MODE?' is always answerable.
    """
    text, err = llm.chat(prompt, system=system, temperature=0.2)
    if err:
        print(f"[AGENT] LLM unavailable: {err}")
    return text, err


# ── Demo reasoning fallback ────────────────────────────────────────────────────
def _demo_reasoning(
    machine_id: str,
    query: str,
    vision_result: dict,
    rag_results: list,
    history: list,
) -> str:
    return f"""DEMO MODE — SIMULATED RESULT

Machine: {machine_id}

Based on visual inspection and retrieved maintenance documentation:

Visual Observation:
{vision_result.get('observations', 'No visual data.')}

Possible Issue:
Potential seal wear and bearing degradation indicated by visual cues. This is a POSSIBLE finding
and requires physical verification by a qualified technician.

Risk Level: {vision_result.get('risk_level', 'MEDIUM')}

Evidence from Knowledge Base:
{chr(10).join(f"• {r.get('document','')}, p.{r.get('page','?')}: {r.get('text','')[:120]}..." for r in rag_results[:2]) if rag_results else '• No documents in knowledge base yet.'}

Recommended Action:
1. Schedule immediate physical inspection of pump seals and bearings.
2. Follow SOP Section 4.2 — Seal Inspection Procedure.
3. Check bearing temperature and vibration levels.
4. If abnormalities confirmed, initiate Maintenance Work Order.
5. Do not operate above 80% capacity until inspection is complete.

Next Action:
Schedule maintenance inspection within 24–48 hours.

Disclaimer:
AI-generated assistance. Final industrial decisions require qualified human verification.
"""


# ── Main agent run ─────────────────────────────────────────────────────────────
def run_agent(
    machine_id: str,
    query: str,
    image_path: Optional[str] = None,
    report_path: Optional[str] = None,
    manual_path: Optional[str] = None,
) -> dict:
    """
    Full agentic pipeline.
    Returns structured result dict consumed by main.py and frontend.
    """
    steps       = []
    tools_used  = []
    uploaded    = []
    demo_mode   = False

    # ── Step 1: Input received ────────────────────────────────────────────────
    steps.append("✓ Input received")

    # ── Step 2: Image analysis ────────────────────────────────────────────────
    vision_result = {}
    if image_path and Path(image_path).exists():
        uploaded.append(Path(image_path).name)
        vision_result = analyze_image(image_path, query)
        tools_used.append("analyze_image")
        if vision_result.get("demo_mode"):
            demo_mode = True
        steps.append("✓ Image analyzed")
    else:
        vision_result = {
            "observations":    "No image provided.",
            "possible_issues": "N/A",
            "risk_level":      "UNKNOWN",
            "confidence":      "N/A",
        }
        steps.append("⚠ No image provided — skipping vision step")

    # ── Step 3: Document ingestion + RAG ─────────────────────────────────────
    rag_results = []

    # Auto-index newly uploaded docs before searching
    new_docs = []
    if report_path and Path(report_path).exists():
        uploaded.append(Path(report_path).name)
        new_docs.append(report_path)
    if manual_path and Path(manual_path).exists():
        uploaded.append(Path(manual_path).name)
        new_docs.append(manual_path)

    if new_docs:
        from backend.rag import build_knowledge_base
        # merge=True: indexing new uploads must NOT wipe previously indexed docs
        kb_build = build_knowledge_base(pdf_paths=new_docs, replace=False)
        tools_used.append("build_knowledge_base")
        steps.append(
            f"✓ {kb_build.get('new_chunks', 0)} new document chunks indexed"
            if kb_build.get("new_chunks") else
            "⚠ Uploaded PDF(s) produced no new indexable text"
        )

    kb_result   = search_knowledge_base(query, top_k=3)
    rag_results = kb_result.get("results", [])
    tools_used.append("search_knowledge_base")
    steps.append(
        "✓ Documents retrieved" if rag_results
        else "⚠ No documents in knowledge base"
    )

    # ── Step 4: Maintenance history ───────────────────────────────────────────
    history_result = get_maintenance_history(machine_id)
    history        = history_result.get("history", [])
    tools_used.append("get_maintenance_history")
    steps.append("✓ Evidence combined")

    # ── Step 5: LLM reasoning ─────────────────────────────────────────────────
    system_prompt = """You are INNOVEXA, a senior industrial AI maintenance assistant.
You help engineers diagnose machine issues based on visual observations and maintenance documents.
Always use cautious language: 'possible', 'potential', 'visual indication', 'requires verification'.
Never claim certainty from visual data alone. Format your response clearly with labelled sections."""

    rag_context = "\n\n".join(
        f"[Doc: {r.get('document','?')}, Page {r.get('page','?')}]\n{r.get('text','')[:400]}"
        for r in rag_results[:3]
    ) if rag_results else "No documents in knowledge base."

    history_text = "\n".join(
        f"• {h['date']} — {h['action']} ({h['status']})"
        for h in history[:3]
    ) if history else "No history available."

    user_prompt = f"""Machine ID: {machine_id}

User Query:
{query}

Visual Observations:
{vision_result.get('observations', 'None')}

Possible Issues (from vision):
{vision_result.get('possible_issues', 'None')}

Risk Level (from vision): {vision_result.get('risk_level', 'UNKNOWN')}

Relevant Knowledge Base Evidence:
{rag_context}

Recent Maintenance History:
{history_text}

Based on all the above, provide a structured maintenance recommendation with:
1. Summary of Visual Observation
2. Possible Issue (cautious language)
3. Risk Level Assessment
4. Recommended Actions (numbered steps)
5. Next Immediate Action
6. Safety Disclaimer
"""

    llm_response, llm_error = _call_llm(user_prompt, system_prompt)
    active_model = llm.text_model() or LLM_MODEL

    if llm_response:
        steps.append(f"✓ Agent reasoning completed ({active_model})")
        reasoning = llm_response
    else:
        demo_mode = True
        steps.append(f"⚠ Local LLM unavailable — DEMO MODE ({llm_error})")
        reasoning = _demo_reasoning(machine_id, query, vision_result, rag_results, history)

    # ── Step 6: Tool selection ─────────────────────────────────────────────────
    steps.append("✓ Automation tool selected")

    # ── Step 7: Recommendation ────────────────────────────────────────────────
    steps.append("✓ Recommendation generated")

    # ── Step 8: Generate report ───────────────────────────────────────────────
    risk  = vision_result.get("risk_level", "MEDIUM")
    issue = vision_result.get("possible_issues", "Potential component issue")

    audit_log_result = save_audit_log(
        user_query    = query,
        uploaded_files= uploaded,
        tools_used    = tools_used,
        model_used    = active_model if not demo_mode else "DEMO_MODE",
        result_summary= reasoning[:200],
        machine_id    = machine_id,
        status        = "demo" if demo_mode else "success",
    )
    audit_id = audit_log_result.get("audit_id", "N/A")
    tools_used.append("save_audit_log")

    report_result = generate_report(
        machine_id          = machine_id,
        visual_observations = vision_result.get("observations", ""),
        possible_issue      = issue,
        risk_level          = risk,
        rag_evidence        = rag_results,
        recommendation      = reasoning,
        uploaded_files      = uploaded,
        audit_id            = audit_id,
        model_used          = active_model if not demo_mode else "DEMO_MODE",
    )
    tools_used.append("generate_report")
    steps.append("✓ Report generated")
    steps.append("✓ Audit log saved")

    # ── Final result ──────────────────────────────────────────────────────────
    return {
        "status":          "demo" if demo_mode else "success",
        "demo_mode":       demo_mode,
        "model_used":      "DEMO_MODE" if demo_mode else active_model,
        "llm_error":       llm_error,
        "vision_error":    vision_result.get("reason") or vision_result.get("error"),
        "machine_id":      machine_id,
        "query":           query,
        "vision":          vision_result,
        "rag_results":     rag_results,
        "maintenance_history": history,
        "reasoning":       reasoning,
        "risk_level":      risk,
        "possible_issue":  issue,
        "report":          report_result,
        "audit_id":        audit_id,
        "steps":           steps,
        "tools_used":      tools_used,
        "uploaded_files":  uploaded,
        "model_used":      LLM_MODEL if not demo_mode else "DEMO_MODE",
    }
