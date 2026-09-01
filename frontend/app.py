"""
INNOVEXA — Sovereign AI Workbench
Streamlit Frontend
"""

import os
import sys
import json
import time
import platform
import requests
from pathlib import Path
from datetime import datetime

import streamlit as st

# ── Project root & path ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

# ── Config ─────────────────────────────────────────────────────────────────────
API_URL      = os.getenv("INNOVEXA_API", "https://innovexa-y8g4.onrender.com")
REPORTS_DIR  = ROOT / "data" / "reports"
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title = "INNOVEXA — Sovereign AI Workbench",
    page_icon  = "⚙️",
    layout     = "wide",
    initial_sidebar_state = "collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS — dark industrial theme
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.cdnfonts.com/css/anthropic-sans');

/* ── Base ── */
* { font-family: 'Anthropic Sans', 'Segoe UI', sans-serif !important; }
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0a0e1a;
    color: #c8d8f0;
    font-family: 'Anthropic Sans', 'Segoe UI', sans-serif;
}
[data-testid="stSidebar"] {
    background-color: #0d1226;
    border-right: 1px solid #1e2d50;
}
/* ── Cards ── */
.inno-card {
    background: linear-gradient(135deg, #111827 0%, #0f172a 100%);
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 18px 22px;
    margin-bottom: 14px;
}
.inno-card-green  { border-left: 4px solid #22c55e; }
.inno-card-yellow { border-left: 4px solid #eab308; }
.inno-card-red    { border-left: 4px solid #ef4444; }
.inno-card-blue   { border-left: 4px solid #3b82f6; }
.inno-card-purple { border-left: 4px solid #a855f7; }

/* ── Status badge ── */
.badge-green  { color:#22c55e; font-weight:700; }
.badge-yellow { color:#eab308; font-weight:700; }
.badge-red    { color:#ef4444; font-weight:700; }
.badge-blue   { color:#60a5fa; font-weight:700; }

/* ── Titles ── */
.inno-title {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 2px;
}
.inno-sub {
    color: #64748b;
    font-size: 0.9rem;
    letter-spacing: 3px;
    text-transform: uppercase;
}
.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #93c5fd;
    border-bottom: 1px solid #1e3a5f;
    padding-bottom: 6px;
    margin-bottom: 12px;
}
/* ── Demo banner ── */
.demo-banner {
    background: #1c1100;
    border: 1px solid #f59e0b;
    border-radius: 8px;
    padding: 10px 16px;
    color: #fcd34d;
    font-weight: 600;
    margin-bottom: 12px;
}
/* ── Steps ── */
.step-done    { color: #22c55e; }
.step-warn    { color: #eab308; }
.step-item    { padding: 4px 0; font-size: 0.9rem; }
/* ── Sidebar nav ── */
.nav-label {
    color: #475569;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    padding: 8px 0 2px 0;
}
/* ── Buttons ── */
[data-testid="stButton"] > button {
    background: linear-gradient(90deg, #1d4ed8, #4f46e5);
    color: #fff;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 10px 24px;
    width: 100%;
}
[data-testid="stButton"] > button:hover {
    background: linear-gradient(90deg, #2563eb, #6d28d9);
}

/* ── Sidebar removed: navigation now lives at the top ── */
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] { display: none !important; }

/* ── Top navigation bar ── */
.top-nav-rule {
    height: 1px;
    background: linear-gradient(90deg, #1e3a5f, #0a0e1a);
    margin: 6px 0 18px 0;
}
[data-testid="stButton"] > button[kind="secondary"],
[data-testid="stBaseButton-secondary"] {
    background: #0f172a !important;
    background-image: none !important;
    border: 1px solid #1e2d50 !important;
    color: #93a7c6 !important;
    font-weight: 600 !important;
    letter-spacing: .4px !important;
    border-radius: 10px !important;
    padding: 8px 10px !important;
    font-size: .8rem !important;
    white-space: nowrap;
    transition: background .18s ease, color .18s ease,
                border-color .18s ease, transform .18s ease;
}
[data-testid="stButton"] > button[kind="secondary"]:hover,
[data-testid="stBaseButton-secondary"]:hover {
    background: #14203a !important;
    color: #dbe8ff !important;
    border-color: #3b82f6 !important;
    transform: translateY(-1px);
}
[data-testid="stButton"] > button[kind="primary"],
[data-testid="stBaseButton-primary"] {
    background: linear-gradient(90deg, #1d4ed8, #4f46e5) !important;
    border: 1px solid #4f46e5 !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    padding: 8px 10px !important;
    font-size: .8rem !important;
    font-weight: 700 !important;
    box-shadow: 0 6px 18px rgba(37, 99, 235, .28);
    white-space: nowrap;
}
/* Responsive: let the tab row wrap into a compact grid on small screens */
@media (max-width: 1100px) {
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        min-width: 150px !important;
    }
    [data-testid="stButton"] > button[kind="secondary"],
    [data-testid="stBaseButton-secondary"],
    [data-testid="stButton"] > button[kind="primary"],
    [data-testid="stBaseButton-primary"] { font-size: .72rem !important; }
}
/* ── Divider ── */
hr { border-color: #1e2d50; }
/* ── Stat cards ── */
.stat-card { transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease; }
.stat-card:hover { transform: translateY(-3px); border-color:#3b82f6; box-shadow:0 8px 22px rgba(37,99,235,.18); }
.stat-label  { font-size:.68rem; letter-spacing:2px; color:#64748b; font-weight:700; }
.stat-value  { font-size:1.02rem; font-weight:800; color:#e2e8f5; margin-top:4px; }
.stat-detail { font-size:.7rem; color:#5b6b86; margin-top:4px; word-break:break-word; }

/* ── Evidence / score bar ── */
.score-bar { height:6px; border-radius:99px; background:#16233d; overflow:hidden; margin-top:6px; }
.score-fill { height:100%; background:linear-gradient(90deg,#22c55e,#38bdf8); }
.chip { display:inline-block; padding:3px 10px; margin:2px 4px 2px 0; border-radius:99px;
        font-size:.7rem; font-weight:700; letter-spacing:1px;
        background:#132039; border:1px solid #1e3a5f; color:#93c5fd; }

/* ── Form inputs (dark enterprise theme) ── */
[data-baseweb="select"] > div, [data-baseweb="input"] > div,
.stTextInput input, .stSelectbox div[role="combobox"] {
    background-color: #0f172a !important;
    border-color: #1e3a5f !important;
    color: #c8d8f0 !important;
}
.stSelectbox [data-baseweb="select"], .stSelectbox [data-baseweb="select"] div,
.stSelectbox [data-baseweb="select"] span, .stSelectbox [data-baseweb="select"] input {
    background-color: #0f172a !important;
    color: #c8d8f0 !important;
}
/* File uploader dropzone */
[data-testid="stFileUploader"] section, [data-testid="stFileUploaderDropzone"] {
    background-color: #0f172a !important;
    border: 1px dashed #1e3a5f !important;
    color: #c8d8f0 !important;
}
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzone"] div { color:#93a7c6 !important; }
[data-testid="stFileUploaderDropzone"] button {
    background-color:#16233d !important; color:#c8d8f0 !important; border:1px solid #1e3a5f !important;
}
/* Text areas */
.stTextArea textarea, [data-baseweb="textarea"] {
    background-color:#0f172a !important; color:#c8d8f0 !important; border-color:#1e3a5f !important;
}
[data-baseweb="popover"] li { background:#0f172a !important; color:#c8d8f0 !important; }
.stCheckbox label, .stSlider label, .stSelectbox label, .stTextInput label { color:#93a7c6 !important; }

/* ── Metric ── */
[data-testid="stMetric"] {
    background: #111827;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
# NOTE on performance: every page switch is a full Streamlit script rerun, and
# this app used to call the backend (/health, /kb-status, /reports, ...)
# fresh — sometimes twice per rerun — with multi-second timeouts. That is what
# caused the long "buffering" pause when navigating between pages, especially
# when the backend was slow or offline. We fix this by (1) short-TTL caching
# every network call so repeated reruns reuse the last known result instead of
# re-hitting the network, and (2) using short timeouts so an offline backend
# fails fast instead of stalling navigation.
HEALTH_TTL   = 6     # seconds — sidebar + dashboard status
DATA_TTL     = 12    # seconds — kb status / reports / audit logs listings
REPORT_TTL   = 60    # seconds — individual report text rarely changes
REQ_TIMEOUT  = 10     # backend /health is fast now, but allow for cold start


@st.cache_data(ttl=HEALTH_TTL, show_spinner=False)
def api_health():
    """
    Backend health. Retries once with a longer timeout: the first request after
    `uvicorn` starts (or after the embedding model loads) can be slow, and a
    single short-timeout attempt used to make a perfectly healthy backend show
    up as OFFLINE in the UI.
    """
    last_error = None
    for timeout in (REQ_TIMEOUT, REQ_TIMEOUT * 2):
        try:
            r = requests.get(f"{API_URL}/health", timeout=timeout)
            if r.status_code == 200:
                data = r.json()
                data["_reachable"] = True
                return data
            last_error = f"HTTP {r.status_code}"
        except Exception as exc:
            last_error = type(exc).__name__
    st.session_state["_health_error"] = last_error
    return None


def health_hint() -> str:
    err = st.session_state.get("_health_error") or ""
    if "ConnectionError" in err:
        return f"No server listening on {API_URL} — start it with `uvicorn backend.main:app --reload`."
    if "Timeout" in err:
        return f"{API_URL} accepted the connection but did not answer in time."
    return f"Backend unreachable ({err or 'unknown error'})."


@st.cache_data(ttl=HEALTH_TTL, show_spinner=False)
def ollama_ok():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=REQ_TIMEOUT)
        return r.status_code == 200
    except Exception:
        return False


def status_dot(ok: bool, labels=("● Online", "● Offline")):
    if ok:
        return f'<span class="badge-green">{labels[0]}</span>'
    return f'<span class="badge-red">{labels[1]}</span>'


def risk_color(risk: str):
    r = risk.upper()
    if "CRITICAL" in r: return "badge-red"
    if "HIGH"     in r: return "badge-red"
    if "MEDIUM"   in r: return "badge-yellow"
    return "badge-green"


def post_analyze(machine_id, query, img_file, report_file, manual_file):
    files = {}
    data  = {"machine_id": machine_id, "query": query}
    if img_file:
        files["image"] = (img_file.name, img_file.getvalue(), img_file.type)
    if report_file:
        files["report_pdf"] = (report_file.name, report_file.getvalue(), report_file.type)
    if manual_file:
        files["manual_pdf"] = (manual_file.name, manual_file.getvalue(), manual_file.type)
    try:
        r = requests.post(f"{API_URL}/analyze", data=data, files=files, timeout=300)
        result = r.json()
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
    # Analysis creates a new report + audit log entry — refresh cached listings.
    get_reports.clear()
    get_audit_logs.clear()
    return result


def post_maintenance_task(machine_id, issue, priority, recommendation):
    try:
        r = requests.post(
            f"{API_URL}/maintenance-task",
            data={"machine_id": machine_id, "issue": issue,
                  "priority": priority, "recommendation": recommendation},
            timeout=30,
        )
        return r.json()
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@st.cache_data(ttl=DATA_TTL, show_spinner=False)
def get_reports():
    try:
        r = requests.get(f"{API_URL}/reports", timeout=6)
        return r.json().get("reports", [])
    except Exception:
        return []


@st.cache_data(ttl=DATA_TTL, show_spinner=False)
def get_audit_logs():
    try:
        r = requests.get(f"{API_URL}/audit-logs", timeout=6)
        return r.json().get("audit_logs", [])
    except Exception:
        return []


@st.cache_data(ttl=REPORT_TTL, show_spinner=False)
def get_report_text(filename):
    try:
        r = requests.get(f"{API_URL}/reports/{filename}", timeout=6)
        return r.text if r.status_code == 200 else ""
    except Exception:
        return ""


def build_kb(files):
    try:
        file_tuples = [("files", (f.name, f.getvalue(), f.type)) for f in files]
        r = requests.post(f"{API_URL}/build-kb", files=file_tuples, timeout=120)
        result = r.json()
    except Exception as exc:
        result = {"status": "error", "error": str(exc)}
    # Invalidate cached KB status so the UI reflects the new documents immediately.
    get_kb_status.clear()
    return result


@st.cache_data(ttl=DATA_TTL, show_spinner=False)
def get_kb_status():
    try:
        r = requests.get(f"{API_URL}/kb-status", timeout=6)
        return r.json()
    except Exception:
        return {"indexed": False, "doc_count": 0, "documents": []}


# ══════════════════════════════════════════════════════════════════════════════
# TOP NAVIGATION (replaces the old left sidebar navigation)
# ══════════════════════════════════════════════════════════════════════════════
NAV_ITEMS = [
    ("dashboard",           "🏠  Dashboard"),
    ("industrial-analysis", "🔬  Industrial Analysis"),
    ("knowledge-base",      "📚  Knowledge Base"),
    ("agent-activity",      "🤖  Agent Activity"),
    ("reports",             "📄  Reports"),
    ("audit-logs",          "🗂  Audit Logs"),
    ("system-status",       "⚙  System Status"),
]
EXTRA_PAGES = {"settings": "⚙  Settings"}
ALL_PAGES = dict(NAV_ITEMS)
ALL_PAGES.update(EXTRA_PAGES)


def current_slug() -> str:
    slug = st.query_params.get("page", "dashboard")
    return slug if slug in ALL_PAGES else "dashboard"


def go_to(slug: str):
    st.query_params["page"] = slug


active = current_slug()
page = ALL_PAGES[active]  # page bodies below match on the label text

# Header row: logo/title on the left, notifications + settings on the right
head_l, head_r = st.columns([0.68, 0.32])
with head_l:
    st.markdown('<div class="inno-title">⚙ INNOVEXA</div>', unsafe_allow_html=True)
    st.markdown('<div class="inno-sub">Sovereign Industrial AI Workbench — Smart Automation</div>',
                unsafe_allow_html=True)
with head_r:
    a1, a2, a3 = st.columns([0.2, 0.22, 0.58])
    with a2:
        st.button("🔔", key="nav_bell", help="Notifications", use_container_width=True)
    with a3:
        if st.button("⚙️ Settings", key="nav_settings",
                     type="primary" if active == "settings" else "secondary",
                     use_container_width=True):
            go_to("settings")
            st.rerun()

# Navigation tabs
nav_cols = st.columns(len(NAV_ITEMS))
for col, (slug, label) in zip(nav_cols, NAV_ITEMS):
    with col:
        if st.button(label, key=f"nav_{slug}", use_container_width=True,
                     type="primary" if slug == active else "secondary"):
            go_to(slug)
            st.rerun()
st.markdown('<div class="top-nav-rule"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if "Dashboard" in page:
    health = st.session_state.get("_health")
    if health is None:
        health = api_health()
        st.session_state["_health"] = health

    st.markdown("<br>", unsafe_allow_html=True)


    # Status row (reuse the value already fetched once in the sidebar this run)
    health     = st.session_state.get("_health") or {}
    comps      = health.get("components", {})
    llm_status = comps.get("local_llm", {}).get("status", "offline")
    rag_status = comps.get("rag",       {}).get("status", "offline")
    vis_status = comps.get("vision",    {}).get("status", "offline")

    llm_meta = comps.get("local_llm", {})
    rag_meta = comps.get("rag", {})
    vis_meta = comps.get("vision", {})

    def stat_card(css, label, status, ok, detail):
        icon = "🟢" if ok else "🔴"
        return (f'<div class="inno-card {css} stat-card">'
                f'<div class="stat-label">{label}</div>'
                f'<div class="stat-value">{icon} {status.upper()}</div>'
                f'<div class="stat-detail">{detail}</div></div>')

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(stat_card("inno-card-blue", "LOCAL AI", llm_status,
                              llm_status == "online",
                              llm_meta.get("model") or "no model"), unsafe_allow_html=True)
    with col2:
        st.markdown(stat_card("inno-card-green", "RAG", rag_status,
                              rag_status in ("ready", "empty"),
                              f"{rag_meta.get('docs', 0)} docs · {rag_meta.get('chunks', 0)} chunks"),
                    unsafe_allow_html=True)
    with col3:
        st.markdown(stat_card("inno-card-purple", "VISION", vis_status,
                              vis_status == "online",
                              vis_meta.get("model") or "no vision model"), unsafe_allow_html=True)
    with col4:
        st.markdown(stat_card("inno-card-blue", "AGENT",
                              "ready" if health else "standby", bool(health),
                              "sense → reason → act"), unsafe_allow_html=True)
    with col5:
        st.markdown('<div class="inno-card inno-card-yellow stat-card">'
                    '<div class="stat-label">DATA MODE</div>'
                    '<div class="stat-value">🔐 ON-PREMISE</div>'
                    '<div class="stat-detail">zero cloud calls</div></div>',
                    unsafe_allow_html=True)

    if not health:
        st.error(f"⚠️ {health_hint()}")
    elif llm_status != "online":
        st.warning(f"🎭 DEMO MODE — {llm_meta.get('reason') or 'local LLM offline'}")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div class="inno-card" style="text-align:center; padding:30px;">
        <div style="font-size:1.3rem; font-weight:700; color:#93c5fd; letter-spacing:3px;">
            ⚡ SMART AUTOMATION
        </div>
        <div style="color:#64748b; margin-top:8px; font-size:1rem; letter-spacing:2px;">
            Sense → Retrieve → Reason → Act → Record
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Workflow diagram
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔄 System Workflow</div>', unsafe_allow_html=True)
    cols = st.columns(9)
    steps = ["📷 Image", "→", "👁 Vision", "→", "📄 RAG", "→", "🤖 Agent", "→", "📋 Report"]
    for col, s in zip(cols, steps):
        with col:
            st.markdown(f'<div style="text-align:center;color:#60a5fa;font-weight:600;">{s}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="inno-card" style="font-size:0.85rem;color:#475569;">🔐 <b>ON-PREMISE DATA MODE</b> — All uploaded files, AI processing, and reports remain strictly local. No data is transmitted to cloud services.</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: INDUSTRIAL ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif "Industrial Analysis" in page:
    st.markdown('<div class="section-title">🔬 INDUSTRIAL ANALYSIS</div>', unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 2])

    with col_left:
        machine_id = st.text_input("Machine ID", value="Industrial Pump P-102")
        img_file   = st.file_uploader("📷 Upload Machine Image", type=["jpg","jpeg","png","bmp","webp"])
        report_file= st.file_uploader("📄 Upload Maintenance Report (PDF)", type=["pdf"])
        manual_file= st.file_uploader("📘 Upload Manual / SOP (PDF)", type=["pdf"])
        query      = st.text_area(
            "💬 Ask the AI:",
            value="Analyze this pump condition and recommend the next maintenance action.",
            height=100,
        )

        if img_file:
            st.image(img_file, caption="Uploaded Image", use_container_width=True)

        analyze_btn = st.button("⚡ ANALYZE", use_container_width=True)

    with col_right:
        if analyze_btn:
            health = api_health()
            if not health:
                st.error("⚠️ Backend is not running. Start it with: `uvicorn backend.main:app --reload`")
            else:
                with st.spinner("🔄 Running agentic AI pipeline..."):
                    result = post_analyze(machine_id, query, img_file, report_file, manual_file)

                st.session_state["last_result"] = result

                if result.get("demo_mode"):
                    st.markdown('<div class="demo-banner">⚠ DEMO MODE — SIMULATED RESULT (Local LLM / Vision not available)</div>', unsafe_allow_html=True)

                vision  = result.get("vision",  {})
                rag     = result.get("rag_results", [])
                reason  = result.get("reasoning", "No reasoning generated.")
                risk    = result.get("risk_level", "UNKNOWN")

                # Main result cards
                st.markdown('<div class="section-title">🤖 AI ANALYSIS</div>', unsafe_allow_html=True)

                r1, r2 = st.columns(2)
                with r1:
                    risk_cls = risk_color(risk)
                    st.markdown(f"""
                    <div class="inno-card inno-card-blue">
                        <b>👁 Visual Observation</b><br><br>
                        {vision.get('observations','No image analysis.').replace(chr(10),'<br>')}
                    </div>""", unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="inno-card inno-card-yellow">
                        <b>⚠ Possible Issue</b><br><br>
                        {vision.get('possible_issues','N/A').replace(chr(10),'<br>')}
                    </div>""", unsafe_allow_html=True)

                with r2:
                    st.markdown(f"""
                    <div class="inno-card">
                        <b>🎯 Risk Level</b><br>
                        <span class="{risk_cls}" style="font-size:1.4rem;">{risk}</span>
                        &nbsp;&nbsp;
                        <b>Confidence:</b> {vision.get('confidence','N/A')}
                    </div>""", unsafe_allow_html=True)

                    if rag:
                        st.markdown('<div class="inno-card inno-card-green"><b>📚 RAG Sources</b><br>', unsafe_allow_html=True)
                        for i, r in enumerate(rag, 1):
                            st.markdown(f"**[{i}]** `{r.get('document','?')}` — Page {r.get('page','?')}")
                            st.caption(r.get("text","")[:200] + "…")
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="inno-card"><b>📚 RAG Sources</b><br><i>No documents in knowledge base. Upload PDFs in the Knowledge Base page.</i></div>', unsafe_allow_html=True)

                # Recommendation
                st.markdown('<div class="section-title">✅ Recommended Action</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="inno-card inno-card-green">{reason.replace(chr(10),"<br>")}</div>', unsafe_allow_html=True)

                # Agent steps
                st.markdown('<div class="section-title">🤖 Agent Activity</div>', unsafe_allow_html=True)
                steps = result.get("steps", [])
                steps_html = "".join(
                    f'<div class="step-item {"step-warn" if "⚠" in s else "step-done"}">{s}</div>'
                    for s in steps
                )
                st.markdown(f'<div class="inno-card">{steps_html}</div>', unsafe_allow_html=True)

                # Automation buttons
                st.markdown('<div class="section-title">⚡ Automation</div>', unsafe_allow_html=True)
                btn1, btn2 = st.columns(2)
                with btn1:
                    if st.button("📋 GENERATE MAINTENANCE REPORT"):
                        rpt = result.get("report", {})
                        if rpt.get("status") == "success":
                            st.success(f"Report saved: {rpt.get('filename','')}")
                        else:
                            st.warning("Report already generated during analysis.")

                with btn2:
                    if st.button("🔧 CREATE MAINTENANCE TASK"):
                        task_r = post_maintenance_task(
                            machine_id     = machine_id,
                            issue          = result.get("possible_issue","Potential issue"),
                            priority       = risk,
                            recommendation = reason[:500],
                        )
                        if task_r.get("status") == "success":
                            task = task_r["task"]
                            st.success(f"Task created: {task['task_id']} | Priority: {task['priority']}")
                        else:
                            st.error("Failed to create task.")

        elif "last_result" not in st.session_state:
            st.markdown("""
            <div class="inno-card" style="text-align:center;padding:40px;">
                <div style="font-size:2rem;">🤖</div>
                <div style="color:#475569;margin-top:12px;">
                    Upload files and click <b>ANALYZE</b> to start the agentic workflow.
                </div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: KNOWLEDGE BASE
# ══════════════════════════════════════════════════════════════════════════════
elif "Knowledge Base" in page:
    st.markdown('<div class="section-title">📚 KNOWLEDGE BASE</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown('<div class="inno-card inno-card-blue"><b>Upload Industrial PDF</b></div>', unsafe_allow_html=True)
        pdfs = st.file_uploader("Upload PDFs (maintenance manuals, SOPs, reports)", type=["pdf"], accept_multiple_files=True)
        if st.button("📥 BUILD / UPDATE KNOWLEDGE BASE"):
            if pdfs:
                with st.spinner("Indexing documents…"):
                    r = build_kb(pdfs)
                if r.get("status") == "success":
                    st.success(f"✅ Indexed {r.get('doc_count',0)} document(s) — {r.get('chunk_count',0)} chunks.")
                else:
                    st.warning(r.get("message", str(r)))
            else:
                st.warning("Please upload at least one PDF.")

    with col2:
        kb = get_kb_status()
        st.markdown('<div class="section-title">📄 Documents in Knowledge Base</div>', unsafe_allow_html=True)
        docs = kb.get("documents", [])
        if docs:
            for doc in docs:
                st.markdown(f"""
                <div class="inno-card inno-card-green">
                    <b>📄 {doc['filename']}</b><br>
                    Pages: {doc['pages']} &nbsp;|&nbsp; Chunks: {doc['chunks']} &nbsp;|&nbsp;
                    <span class="badge-green">✓ {doc['status']}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="inno-card"><i>No documents indexed yet.</i></div>', unsafe_allow_html=True)

        st.markdown(f'<div style="font-size:0.85rem;color:#475569;">Total docs: {kb.get("doc_count",0)} | Chunks: {kb.get("chunk_count",0)}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AGENT ACTIVITY
# ══════════════════════════════════════════════════════════════════════════════
elif "Agent Activity" in page:
    st.markdown('<div class="section-title">🤖 AGENT ACTIVITY</div>', unsafe_allow_html=True)

    result = st.session_state.get("last_result")
    if result:
        if result.get("demo_mode"):
            st.markdown('<div class="demo-banner">⚠ DEMO MODE — SIMULATED RESULT</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-title">Pipeline Steps</div>', unsafe_allow_html=True)
            steps = result.get("steps", [])
            for s in steps:
                cls = "step-warn" if "⚠" in s else "step-done"
                st.markdown(f'<div class="step-item {cls}">{s}</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="section-title">Tools Used</div>', unsafe_allow_html=True)
            for t in result.get("tools_used", []):
                st.markdown(f'<div class="inno-card" style="padding:8px 14px;">🔧 <code>{t}</code></div>', unsafe_allow_html=True)

            st.markdown(f"""
            <div class="inno-card inno-card-blue" style="margin-top:12px;">
                <b>Model:</b> {result.get('model_used','N/A')}<br>
                <b>Machine:</b> {result.get('machine_id','N/A')}<br>
                <b>Audit ID:</b> {result.get('audit_id','N/A')}
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-title">Agent Reasoning</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="inno-card">{result.get("reasoning","").replace(chr(10),"<br>")}</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="inno-card" style="text-align:center;padding:40px;">
            <div style="color:#475569;">Run an analysis first to see agent activity.</div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: REPORTS
# ══════════════════════════════════════════════════════════════════════════════
elif "Reports" in page:
    st.markdown('<div class="section-title">📄 REPORTS</div>', unsafe_allow_html=True)

    reports = get_reports()
    if reports:
        for rpt in reports:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f'<div class="inno-card inno-card-blue"><b>📄 {rpt["filename"]}</b><br><span style="font-size:0.8rem;color:#64748b;">{rpt["created"][:19]} | {rpt["size_kb"]} KB</span></div>', unsafe_allow_html=True)
            with col2:
                if st.button("👁 View", key=f"view_{rpt['filename']}"):
                    text = get_report_text(rpt["filename"])
                    st.text_area("Report", value=text, height=400)
            with col3:
                text = get_report_text(rpt["filename"])
                st.download_button(
                    "⬇ Download",
                    data=text,
                    file_name=rpt["filename"],
                    mime="text/plain",
                    key=f"dl_{rpt['filename']}",
                )
    else:
        st.markdown('<div class="inno-card"><i>No reports generated yet. Run an analysis first.</i></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AUDIT LOGS
# ══════════════════════════════════════════════════════════════════════════════
elif "Audit Logs" in page:
    st.markdown('<div class="section-title">🗂 AUDIT LOGS</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.85rem;color:#475569;margin-bottom:12px;">All AI actions are logged locally for traceability and compliance.</div>', unsafe_allow_html=True)

    logs = get_audit_logs()
    if logs:
        for log in logs:
            st.markdown(f"""
            <div class="inno-card {"inno-card-green" if log.get("status")=="success" else "inno-card-yellow"}">
                <b>{log.get('audit_id','?')}</b> &nbsp;|&nbsp;
                {log.get('timestamp','')[:19]} &nbsp;|&nbsp;
                Machine: <b>{log.get('machine_id','?')}</b> &nbsp;|&nbsp;
                Model: <code>{log.get('model_used','?')}</code> &nbsp;|&nbsp;
                <span class="{'badge-green' if log.get('status')=='success' else 'badge-yellow'}">
                    {log.get('status','?').upper()}
                </span><br>
                <span style="font-size:0.85rem;color:#94a3b8;">
                    Query: {log.get('user_query','')[:100]}
                </span><br>
                <span style="font-size:0.8rem;color:#475569;">
                    Tools: {', '.join(log.get('tools_used',[]))}
                </span>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="inno-card"><i>No audit records yet. Run an analysis to generate logs.</i></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SYSTEM STATUS
# ══════════════════════════════════════════════════════════════════════════════
elif "System Status" in page:
    st.markdown('<div class="section-title">⚙ SYSTEM STATUS</div>', unsafe_allow_html=True)

    health   = st.session_state.get("_health") or {}
    comps    = health.get("components", {})
    llm_info = comps.get("local_llm", {})
    rag_info = comps.get("rag",       {})
    vis_info = comps.get("vision",    {})

    def status_badge(s):
        s = str(s).lower()
        if s in ("online","ready","ok","success"): return "🟢 READY"
        if s in ("empty", "warning"):              return "🟡 WARNING"
        return "🔴 OFFLINE"

    items = [
        ("Python Version",  sys.version.split()[0],          "🟢 READY"),
        ("Operating System",platform.system(),               "🟢 READY"),
        ("Backend API",     "FastAPI",                        status_badge(health.get("status","offline"))),
        ("Local LLM",       "Ollama",                         status_badge(llm_info.get("status","offline"))),
        ("Model Name",      llm_info.get("model","N/A"),      status_badge(llm_info.get("status","offline"))),
        ("RAG Status",      f"{rag_info.get('docs',0)} docs", status_badge(rag_info.get("status","offline"))),
        ("Vision Status",   "Multimodal",                     status_badge(vis_info.get("status","offline"))),
        ("Storage Status",  "Local / On-Premise",             "🟢 READY"),
        ("Data Mode",       "ON-PREMISE",                     "🔐 SECURE"),
    ]

    for label, value, badge in items:
        st.markdown(f"""
        <div class="inno-card" style="padding:12px 18px; display:flex; justify-content:space-between; align-items:center;">
            <span style="color:#93c5fd; font-weight:600;">{label}</span>
            <span style="color:#64748b;">{value}</span>
            <span>{badge}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="inno-card inno-card-blue" style="font-size:0.85rem;">🔐 <b>ON-PREMISE DATA MODE</b><br>Confidential files are processed locally. No data is transmitted to cloud services. All AI inference runs on local hardware via Ollama.</div>', unsafe_allow_html=True)

    # Ollama model list
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=4)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            st.markdown('<div class="section-title" style="margin-top:20px;">Available Ollama Models</div>', unsafe_allow_html=True)
            for m in models:
                st.markdown(f'<div class="inno-card" style="padding:8px 14px;">🤖 <code>{m}</code></div>', unsafe_allow_html=True)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
elif "Settings" in page:
    st.markdown('<div class="section-title">⚙ SETTINGS</div>', unsafe_allow_html=True)
    st.caption("Preferences below are UI-level only. Options marked *not yet wired* "
               "are prepared for future backend integration and do not change system behaviour.")

    health   = st.session_state.get("_health") or {}
    comps    = health.get("components", {})
    llm_info = comps.get("local_llm", {})
    rag_info = comps.get("rag", {})
    vis_info = comps.get("vision", {})

    def kv_row(label, value, badge=""):
        st.markdown(f"""
        <div class="inno-card" style="padding:12px 18px; display:flex; justify-content:space-between; align-items:center;">
            <span style="color:#93c5fd; font-weight:600;">{label}</span>
            <span style="color:#64748b;">{value}</span>
            <span>{badge}</span>
        </div>""", unsafe_allow_html=True)

    # ── GENERAL ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title" style="margin-top:18px;">GENERAL</div>', unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1:
        st.markdown('<div class="inno-card inno-card-blue"><b>Application preferences</b></div>', unsafe_allow_html=True)
        st.selectbox("Default landing page", [lbl.strip() for _, lbl in NAV_ITEMS],
                     index=0, key="set_landing", help="Not yet wired — Dashboard remains the default page.")
        st.text_input("Backend API URL", value=API_URL, key="set_api_url", disabled=True,
                      help="Configured with the INNOVEXA_API environment variable.")
    with g2:
        st.markdown('<div class="inno-card inno-card-blue"><b>Dashboard preferences</b></div>', unsafe_allow_html=True)
        st.checkbox("Show status cards on dashboard", value=True, key="set_show_status",
                    help="Not yet wired — status cards are always shown.")
        st.slider("Status refresh interval (seconds)", 5, 120, HEALTH_TTL, key="set_refresh",
                  help="Not yet wired — current cache TTL is shown for reference.")

    # ── AI CONFIGURATION ──────────────────────────────────────────────────────
    st.markdown('<div class="section-title" style="margin-top:18px;">AI CONFIGURATION</div>', unsafe_allow_html=True)
    kv_row("LLM runtime", "Ollama (local)",
           "🟢 ONLINE" if llm_info.get("status") == "online" else "🔴 OFFLINE")
    kv_row("Active text model", llm_info.get("model") or "not detected", "")
    kv_row("Active vision model", vis_info.get("model") or "not detected",
           "🟢 ONLINE" if vis_info.get("status") == "online" else "🔴 OFFLINE")
    kv_row("RAG index", f"{rag_info.get('docs', 0)} docs · {rag_info.get('chunks', 0)} chunks",
           "🟢 READY" if rag_info.get("status") == "ready" else "🟡 EMPTY")
    a1c, a2c = st.columns(2)
    with a1c:
        st.markdown('<div class="inno-card inno-card-purple"><b>RAG configuration</b></div>', unsafe_allow_html=True)
        st.slider("Retrieved passages (top-k)", 1, 10, 4, key="set_topk",
                  help="Not yet wired — retrieval depth is set by the backend.")
    with a2c:
        st.markdown('<div class="inno-card inno-card-purple"><b>Agent preferences</b></div>', unsafe_allow_html=True)
        st.checkbox("Show sense → reason → act trace", value=True, key="set_trace",
                    help="Not yet wired — the agent trace is always shown on Agent Activity.")
    if st.button("🔄 Re-check AI components", key="set_recheck"):
        api_health.clear()
        get_kb_status.clear()
        st.session_state["_health"] = api_health()
        st.rerun()

    # ── SYSTEM ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title" style="margin-top:18px;">SYSTEM</div>', unsafe_allow_html=True)
    kv_row("Backend API", "FastAPI",
           "🟢 ONLINE" if health else "🔴 OFFLINE")
    kv_row("Connection", API_URL, "🟢 REACHABLE" if health else "🔴 UNREACHABLE")
    kv_row("Ollama endpoint", OLLAMA_URL, "🟢 REACHABLE" if ollama_ok() else "🔴 UNREACHABLE")
    kv_row("Python version", sys.version.split()[0], "🟢 READY")
    kv_row("Operating system", platform.system(), "🟢 READY")
    if not health:
        st.warning(f"⚠ {health_hint()}")

    # ── DATA & PRIVACY ────────────────────────────────────────────────────────
    st.markdown('<div class="section-title" style="margin-top:18px;">DATA &amp; PRIVACY</div>', unsafe_allow_html=True)
    d1, d2 = st.columns(2)
    with d1:
        st.markdown('<div class="inno-card inno-card-green"><b>Data processing preferences</b></div>', unsafe_allow_html=True)
        st.checkbox("Keep generated reports on disk", value=True, key="set_keep_reports",
                    help="Not yet wired — reports are stored under data/reports.")
        st.checkbox("Write audit log entries", value=True, key="set_audit",
                    help="Not yet wired — audit logging is always enabled.")
    with d2:
        st.markdown('<div class="inno-card inno-card-green"><b>Local / on-premise data mode</b></div>', unsafe_allow_html=True)
        st.markdown('<div class="inno-card" style="font-size:0.85rem;">🔐 <b>ON-PREMISE DATA MODE</b><br>'
                    'Confidential files are processed locally. No data is transmitted to cloud services.</div>',
                    unsafe_allow_html=True)

    # ── APPEARANCE ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title" style="margin-top:18px;">APPEARANCE</div>', unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1:
        st.selectbox("Theme", ["Industrial Dark (default)"], index=0, key="set_theme",
                     help="Not yet wired — the dark enterprise theme is currently fixed.")
    with p2:
        st.selectbox("Layout density", ["Comfortable", "Compact"], index=0, key="set_density",
                     help="Not yet wired — spacing is fixed for now.")
