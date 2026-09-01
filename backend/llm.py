"""
INNOVEXA - llm.py
Single shared Ollama client for the whole backend.

Fixes the three long-standing issues:
  1. "Backend OFFLINE" in the frontend  -> status probes are cached and use a
     very short timeout, so /health always answers in well under a second
     even when Ollama is unreachable / hanging.
  2. "LLM offline / always DEMO MODE"   -> the configured model no longer has to
     exist. We read the installed model list from Ollama and auto-resolve the
     best available text model (and vision model), so a machine with only
     e.g. llama3 or qwen2.5 still gets real answers instead of DEMO MODE.
  3. Silent failures                    -> every failure returns a human
     readable reason that is surfaced to the UI.
"""

from __future__ import annotations

import os
import time
import json
import logging
from typing import Optional, List, Dict, Tuple

import requests

logger = logging.getLogger("innovexa.llm")

OLLAMA_URL    = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
TEXT_MODEL    = os.getenv("OLLAMA_MODEL", "").strip()
VISION_MODEL  = os.getenv("VISION_MODEL", "").strip()

STATUS_TIMEOUT = float(os.getenv("OLLAMA_STATUS_TIMEOUT", "1.5"))   # fast fail
GEN_TIMEOUT    = float(os.getenv("OLLAMA_GEN_TIMEOUT", "180"))
STATUS_TTL     = float(os.getenv("OLLAMA_STATUS_TTL", "5"))          # seconds

# Preference order used when the configured model is missing.
TEXT_PREFS   = ["mistral", "llama3.2", "llama3.1", "llama3", "qwen2.5",
                "qwen2", "gemma2", "gemma", "phi3", "phi", "tinyllama"]
VISION_PREFS = ["llava-phi3", "llava-llama3", "llava", "bakllava",
                "moondream", "minicpm-v", "qwen2-vl", "gemma3"]

_cache: Dict[str, object] = {"ts": 0.0, "value": None}


# ────────────────────────────────────────────────────────────────────────────────
# Status (cached, fast-fail)
# ────────────────────────────────────────────────────────────────────────────────
def probe(force: bool = False) -> dict:
    """
    Returns:
      {running, models, text_model, vision_model, vision_available, reason}
    Cached for STATUS_TTL seconds so /health never blocks the UI.
    """
    now = time.time()
    cached = _cache.get("value")
    if cached and not force and (now - float(_cache["ts"])) < STATUS_TTL:
        return cached  # type: ignore[return-value]

    info = {
        "running": False,
        "models": [],
        "text_model": TEXT_MODEL or None,
        "vision_model": VISION_MODEL or None,
        "vision_available": False,
        "url": OLLAMA_URL,
        "reason": "",
    }

    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=STATUS_TIMEOUT)
        r.raise_for_status()
        models = [m.get("name", "") for m in r.json().get("models", []) if m.get("name")]
        info["running"] = True
        info["models"] = models

        if not models:
            info["reason"] = ("Ollama is running but no models are installed. "
                              "Run:  ollama pull mistral  and  ollama pull llava")
        else:
            info["text_model"]   = _resolve(models, TEXT_MODEL, TEXT_PREFS, vision=False)
            info["vision_model"] = _resolve(models, VISION_MODEL, VISION_PREFS, vision=True)
            info["vision_available"] = info["vision_model"] is not None
            if info["text_model"] is None:
                info["reason"] = ("No usable text model found in Ollama. "
                                  "Run:  ollama pull mistral")
            elif not info["vision_available"]:
                info["reason"] = ("No vision model installed - image analysis will use "
                                  "DEMO MODE. Run:  ollama pull llava")
    except requests.exceptions.ConnectionError:
        info["reason"] = (f"Cannot reach Ollama at {OLLAMA_URL}. "
                          "Start it with:  ollama serve")
    except requests.exceptions.Timeout:
        info["reason"] = f"Ollama at {OLLAMA_URL} did not respond in {STATUS_TIMEOUT}s."
    except Exception as exc:                                   # pragma: no cover
        info["reason"] = f"Ollama status check failed: {exc}"

    _cache["ts"] = now
    _cache["value"] = info
    return info


def _base(name: str) -> str:
    return name.split(":", 1)[0].lower()


def _is_vision(name: str) -> bool:
    n = name.lower()
    return any(v in n for v in VISION_PREFS) or "vl" in n or "vision" in n


def _resolve(models: List[str], configured: str, prefs: List[str], vision: bool) -> Optional[str]:
    """Pick the configured model if installed, otherwise the best match."""
    if configured:
        for m in models:                          # exact tag match
            if m == configured:
                return m
        for m in models:                          # name match ignoring :tag
            if _base(m) == _base(configured):
                return m
    for want in prefs:
        for m in models:
            if _base(m) == want or want in _base(m):
                return m
    pool = [m for m in models if _is_vision(m)] if vision else \
           [m for m in models if not _is_vision(m)]
    return pool[0] if pool else (None if vision else (models[0] if models else None))


def text_model() -> Optional[str]:
    return probe().get("text_model")            # type: ignore[return-value]


def vision_model() -> Optional[str]:
    return probe().get("vision_model")          # type: ignore[return-value]


def is_online() -> bool:
    p = probe()
    return bool(p.get("running")) and bool(p.get("text_model"))


# ────────────────────────────────────────────────────────────────────────────────
# Generation
# ────────────────────────────────────────────────────────────────────────────────
def chat(prompt: str, system: str = "", temperature: float = 0.2) -> Tuple[str, Optional[str]]:
    """
    Returns (text, error). error is None on success.
    Uses /api/chat and transparently falls back to /api/generate for old builds.
    """
    p = probe()
    if not p.get("running"):
        return "", str(p.get("reason") or "Local LLM offline.")
    model = p.get("text_model")
    if not model:
        return "", str(p.get("reason") or "No text model installed in Ollama.")

    messages = ([{"role": "system", "content": system}] if system else []) + \
               [{"role": "user", "content": prompt}]
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": model, "messages": messages, "stream": False,
                  "options": {"temperature": temperature}},
            timeout=GEN_TIMEOUT,
        )
        if r.status_code == 404:
            return _generate(model, (system + "\n\n" + prompt).strip(), temperature)
        r.raise_for_status()
        content = (r.json().get("message") or {}).get("content", "").strip()
        if not content:
            return "", f"Model '{model}' returned an empty response."
        return content, None
    except requests.exceptions.Timeout:
        return "", f"Model '{model}' timed out after {int(GEN_TIMEOUT)}s."
    except requests.exceptions.ConnectionError:
        _cache["ts"] = 0.0
        return "", f"Lost connection to Ollama at {OLLAMA_URL}."
    except Exception as exc:
        return "", f"LLM call failed: {exc}"


def _generate(model: str, prompt: str, temperature: float) -> Tuple[str, Optional[str]]:
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False,
                  "options": {"temperature": temperature}},
            timeout=GEN_TIMEOUT,
        )
        r.raise_for_status()
        return r.json().get("response", "").strip(), None
    except Exception as exc:
        return "", f"LLM call failed: {exc}"


def vision(prompt: str, image_b64: str, temperature: float = 0.1) -> Tuple[str, Optional[str]]:
    p = probe()
    if not p.get("running"):
        return "", str(p.get("reason") or "Local LLM offline.")
    model = p.get("vision_model")
    if not model:
        return "", ("No vision-capable model installed in Ollama. "
                    "Run:  ollama pull llava")
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "images": [image_b64],
                  "stream": False, "options": {"temperature": temperature}},
            timeout=GEN_TIMEOUT,
        )
        r.raise_for_status()
        return r.json().get("response", "").strip(), None
    except requests.exceptions.Timeout:
        return "", f"Vision model '{model}' timed out after {int(GEN_TIMEOUT)}s."
    except requests.exceptions.ConnectionError:
        _cache["ts"] = 0.0
        return "", f"Lost connection to Ollama at {OLLAMA_URL}."
    except Exception as exc:
        return "", f"Vision call failed: {exc}"


def extract_json(raw: str) -> Optional[dict]:
    """Best-effort JSON extraction from an LLM response (fences, prose, etc.)."""
    if not raw:
        return None
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1] if len(text.split("```")) > 1 else text
        text = text[4:] if text.lower().startswith("json") else text
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    start, depth = text.find("{"), 0
    if start == -1:
        return None
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except Exception:
                    return None
    return None
