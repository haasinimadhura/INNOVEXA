"""
INNOVEXA - vision.py
Local multimodal image analysis via Ollama, with auto model resolution.
Falls back to a clearly labelled DEMO MODE result when no vision model exists.
"""

from __future__ import annotations

import base64
from pathlib import Path

from backend import llm

MAX_IMAGE_MB = 20


def _encode_image(image_path: str) -> str:
    with open(image_path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("utf-8")


def _demo_result(image_path: str, reason: str = "") -> dict:
    return {
        "status": "demo",
        "demo_mode": True,
        "model": "DEMO_MODE",
        "image_file": Path(image_path).name if image_path else "n/a",
        "reason": reason,
        "observations": (
            "DEMO MODE - SIMULATED RESULT\n\n"
            "Visual inspection indicates possible surface discolouration and minor "
            "abnormalities on the pump casing. Slight wear pattern observed around "
            "the impeller coupling area. Potential fluid residue visible near the seal joint."
        ),
        "possible_issues": (
            "- Potential seal degradation (visual indication only)\n"
            "- Possible bearing wear - requires tactile/acoustic verification\n"
            "- Minor corrosion on external casing (surface level)"
        ),
        "risk_level": "MEDIUM",
        "confidence": "SIMULATED",
        "next_steps": "Perform detailed physical inspection per SOP Section 4.2.",
    }


PROMPT = """You are an industrial AI inspection assistant analyzing a machine/component image.

User query: {query}

Respond ONLY with valid JSON in exactly this format:
{{
  "observations": "What you actually see - surface condition, colour, wear, damage, fluid traces.",
  "possible_issues": "Possible issues based solely on visual evidence. Use 'possible'/'potential'.",
  "risk_level": "LOW | MEDIUM | HIGH | CRITICAL",
  "confidence": "LOW | MEDIUM | HIGH",
  "next_steps": "Recommended next inspection step."
}}

Do NOT fabricate measurements. Only describe what is visually observable."""


def analyze_image(image_path: str, query: str = "") -> dict:
    """Analyze an image with the local vision model; returns a structured dict."""
    path = Path(image_path or "")
    if not path.exists():
        return {**_demo_result(image_path, f"Image not found: {image_path}"),
                "status": "error", "error": f"Image not found: {image_path}"}

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_IMAGE_MB:
        return _demo_result(image_path, f"Image too large for local vision model ({size_mb:.1f} MB).")

    prompt = PROMPT.format(
        query=query or "Analyze this machine component and identify any visible issues."
    )
    raw, err = llm.vision(prompt, _encode_image(str(path)))
    if err:
        return _demo_result(image_path, err)

    model = llm.vision_model() or "unknown"
    parsed = llm.extract_json(raw)
    if isinstance(parsed, dict) and parsed.get("observations"):
        return {
            "status": "success",
            "demo_mode": False,
            "model": model,
            "image_file": path.name,
            "observations": str(parsed.get("observations", "")).strip(),
            "possible_issues": str(parsed.get("possible_issues", "See observations.")).strip(),
            "risk_level": str(parsed.get("risk_level", "UNKNOWN")).upper().strip(),
            "confidence": str(parsed.get("confidence", "MEDIUM")).upper().strip(),
            "next_steps": str(parsed.get("next_steps", "Manual review recommended.")).strip(),
        }

    # Model replied in prose - still a real (non-demo) result.
    return {
        "status": "success",
        "demo_mode": False,
        "model": model,
        "image_file": path.name,
        "observations": raw or "Vision model returned no text.",
        "possible_issues": "See observations above.",
        "risk_level": "UNKNOWN",
        "confidence": "LOW",
        "next_steps": "Manual review required.",
    }


def check_vision_status() -> dict:
    p = llm.probe()
    return {
        "ollama_running": bool(p.get("running")),
        "vision_available": bool(p.get("vision_available")),
        "available_models": p.get("models", []),
        "configured_model": p.get("vision_model"),
        "reason": p.get("reason", ""),
    }
