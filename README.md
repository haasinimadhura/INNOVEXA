# ⚙ INNOVEXA
## Sovereign On-Premise Agentic AI Workbench
### Using Open-Weight Multimodal LLMs for Confidential Industrial Work

**SIH Internal Hackathon | Theme: Smart Automation**

---

## 1. Project Overview

INNOVEXA is a fully local, on-premise AI workbench that empowers industrial engineers to inspect and maintain machinery using open-weight Large Language Models — with **zero cloud dependency**. All data, models, and AI inference remain on local hardware.

---

## 2. Problem Statement

Industrial facilities handle sensitive operational data — machine manuals, maintenance logs, failure reports — that cannot be uploaded to cloud AI services. Engineers need AI assistance but face data sovereignty and confidentiality constraints.

---

## 3. Smart Automation Theme

INNOVEXA automates the complete inspection pipeline:

```
Sense → Retrieve → Reason → Act → Record
```

- **Sense**: Capture machine images
- **Retrieve**: Pull relevant SOP and maintenance documents via RAG
- **Reason**: Local LLM reasons over combined evidence
- **Act**: Generate recommendations, maintenance tasks, and reports
- **Record**: Audit log every AI action for traceability

---

## 4. Proposed Solution

A local Python application combining:
- **Vision AI** — analyze machine images with a multimodal LLM
- **RAG** — search uploaded industrial PDFs semantically
- **Agentic AI** — orchestrate vision + retrieval + reasoning
- **Automation Tools** — generate reports, tasks, and audit logs
- **Streamlit UI** — modern dark industrial interface

---

## 5. Features

| Feature | Description |
|---|---|
| 🖼 Vision Analysis | Local multimodal model inspects machine images |
| 📚 RAG Pipeline | Semantic search over industrial PDFs (FAISS + sentence-transformers) |
| 🤖 AI Agent | Orchestrates the full sense→reason→act pipeline |
| 📋 Report Generation | Structured industrial maintenance reports saved locally |
| 🔧 Maintenance Tasks | Simulated task creation with priority and tracking |
| 🗂 Audit Logging | Complete traceability of every AI action |
| 🔐 On-Premise | Zero cloud dependency — all data stays local |
| 🎭 Demo Mode | Works even without Ollama for demonstration |

---

## 6. System Workflow

```
USER
  ↓
STREAMLIT WORKBENCH
  ↓
FASTAPI BACKEND
  ↓
INPUT PROCESSING
  ↓
┌──────────────────────────────┐
│  IMAGE          DOCUMENT     │
│    ↓                ↓        │
│  VISION          RAG         │
│    ↓                ↓        │
│  VISUAL          EVIDENCE    │
│  OBSERVATION                 │
│         ↓                    │
└─────────┬────────────────────┘
          ↓
      AI AGENT
          ↓
   PLAN + REASON
          ↓
     TOOL SELECTION
          ↓
 AUTOMATION EXECUTION
          ↓
 RECOMMENDATION
          ↓
 REPORT GENERATION
          ↓
     AUDIT LOG
```

---

## 7. Architecture

```
INNOVEXA
    │
    ▼
┌─────────────────┐
│   STREAMLIT UI  │  frontend/app.py
└────────┬────────┘
         │ HTTP REST
         ▼
┌─────────────────┐
│     FASTAPI     │  backend/main.py
└────────┬────────┘
         │
┌────────┴────────┐
│                 │
▼                 ▼
VISION           RAG
vision.py        rag.py
│                 │
└────────┬────────┘
         ▼
      AGENT
      agent.py
         │
         ▼
      LOCAL LLM
       Ollama
         │
         ▼
       TOOLS
      tools.py
         │
    ┌────┼────┐
    ▼    ▼    ▼
 REPORT TASK AUDIT
         │
  LOCAL STORAGE
```

---

## 8. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI + Uvicorn |
| Local AI | Ollama (Mistral, LLaVA, etc.) |
| Vision | LLaVA / llava-phi3 via Ollama |
| RAG Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector Store | FAISS (faiss-cpu) |
| PDF Extraction | PyMuPDF (fitz) |
| Image Handling | Pillow |
| Language | Python 3.10+ |

---

## 9. Folder Structure

```
Innovexa/
│
├── backend/
│   ├── __init__.py
│   ├── main.py       ← FastAPI entry point
│   ├── agent.py      ← Agentic AI workflow
│   ├── rag.py        ← RAG pipeline
│   ├── vision.py     ← Image analysis
│   └── tools.py      ← Automation tools
│
├── frontend/
│   └── app.py        ← Streamlit UI
│
├── data/
│   ├── manuals/      ← Uploaded PDFs (indexed by RAG)
│   ├── reports/      ← Generated maintenance reports
│   └── images/       ← Uploaded machine images
│
├── models/           ← (reserved for local model files)
│
├── requirements.txt
└── README.md
```

---

## 10. Installation

```bash
# Clone or unzip the project
cd Innovexa

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 11. Ollama Setup

```bash
# Install Ollama from https://ollama.com

# Pull a text LLM
ollama pull mistral

# Pull a vision model
ollama pull llava

# Verify
ollama list
```

---

## 12. Running Backend

Open a terminal in the `Innovexa/` folder:

```bash
# Activate venv
.venv\Scripts\activate

# Start FastAPI
uvicorn backend.main:app --reload
```

Backend runs at: http://localhost:8000  
API docs at: http://localhost:8000/docs

---

## 13. Running Frontend

Open a **second** terminal in the `Innovexa/` folder:

```bash
.venv\Scripts\activate

streamlit run frontend/app.py
```

Frontend opens at: http://localhost:8501

---

## 14. Adding Documents

Place industrial PDFs into `data/manuals/` OR upload via the **Knowledge Base** page in the UI.

Click **BUILD / UPDATE KNOWLEDGE BASE** to index them.

---

## 15. Running the Demo

**Demo Scenario — Industrial Pump P-102**

1. Open http://localhost:8501
2. Go to **Industrial Analysis**
3. Machine ID: `Industrial Pump P-102`
4. Upload: pump image (JPG/PNG)
5. Upload: maintenance report PDF
6. Upload: SOP manual PDF
7. Query: `Analyze this pump condition and recommend the next maintenance action.`
8. Click **ANALYZE**
9. View results, generate report, create maintenance task

> If Ollama is not running, DEMO MODE activates automatically with clearly labelled simulated results.

---

## 16. Agent Workflow

```
User Query
    ↓
Understand Request
    ↓
Check Available Inputs
    ↓
Image Analysis (if image exists)
    ↓
RAG Search (if documents exist)
    ↓
Combine Results
    ↓
Local LLM Reasoning
    ↓
Decide Required Action
    ↓
Call Automation Tool
    ↓
Generate Final Recommendation
```

---

## 17. RAG Workflow

```
PDF Upload
    ↓
Text Extraction (PyMuPDF)
    ↓
Text Cleaning
    ↓
Chunking (400 words, 80 overlap)
    ↓
Embeddings (all-MiniLM-L6-v2)
    ↓
FAISS Vector Index
    ↓
Semantic Search
    ↓
Relevant Chunks + Source Info
    ↓
Passed to Agent/LLM
```

---

## 18. Security

- All uploaded files saved under `data/` — local only
- No external API calls for AI (Ollama is local)
- File type and size validation on upload
- Audit trail for every AI action
- Report generation is local text files
- `ON-PREMISE DATA MODE` displayed throughout UI

---

## 19. Team Roles

| Role | Responsibility |
|---|---|
| AI/ML Lead | Agent, RAG, Vision pipeline |
| Backend Dev | FastAPI endpoints, data handling |
| Frontend Dev | Streamlit UI design |
| DevOps | Ollama setup, environment |
| Domain Expert | Industrial use case validation |

---

## 20. Future Scope

- Real-time sensor data integration (IoT)
- Multi-machine fleet monitoring
- Fine-tuned domain-specific LLM
- Predictive maintenance ML models
- Role-based access control
- Mobile inspection app
- Integration with CMMS systems
- Multi-language support
- Edge deployment on industrial hardware

---

## 21. v1.1 Fixes (Backend / LLM / RAG / Frontend)

### Backend showed "OFFLINE" in the frontend
`/health` used to make two blocking Ollama calls (4s + 5s timeouts). With Ollama
not reachable, the endpoint took up to ~9s while the Streamlit client timed out
after 3s — so a perfectly healthy backend was rendered as **Backend ● Offline**.

* All Ollama probing moved into one shared client (`backend/llm.py`) with a
  1.5s fast-fail timeout and a 5s in-memory cache -> `/health` now answers in
  ~0.3s.
* Frontend timeout raised to 10s with one longer retry (cold start / model load).
* The sidebar and dashboard now show the *reason* for any offline component
  instead of a bare red dot.

### LLM issues
* The configured model no longer has to exist. `backend/llm.py` reads the
  installed model list and auto-resolves the best available text model
  (mistral -> llama3.x -> qwen2.5 -> gemma -> phi3 ...) and vision model
  (llava -> llava-phi3 -> bakllava -> moondream ...). No more DEMO MODE just
  because `mistral` was not pulled.
* `/api/chat` falls back to `/api/generate` on older Ollama builds.
* Every failure returns a human-readable reason (`llm_error`) which is surfaced
  in the analysis result and the UI, instead of an empty string.
* New `GET /models` endpoint lists installed models and the active selection.

### RAG issues
* **Data loss fixed:** analysing with a new PDF called
  `build_knowledge_base(pdf_paths=new_docs)`, which rebuilt the index from only
  those files and destroyed every previously indexed document. Indexing is now
  incremental (`replace=False` by default) and merges metadata.
* **Relevance fixed:** FAISS returned L2 distances (lower = better) while the
  numpy fallback returned dot products (higher = better), so scores were
  inconsistent and ranking was wrong on one path. Embeddings are now L2
  normalized and both paths use cosine similarity (`IndexFlatIP` / numpy dot),
  giving comparable 0..1 scores with a low-relevance cut-off.
* **Status fixed:** `/kb-status` read an in-memory chunk list, so it reported
  0 chunks after a restart. It now reports from the persisted index.
* **Self-healing:** a stale or incompatible index (e.g. a pickle holding a FAISS
  object on a machine without `faiss`) previously killed retrieval silently; the
  index is now automatically rebuilt from the PDFs on disk.
* Scanned/image-only PDFs are reported per document instead of failing silently.
* New endpoints: `POST /rebuild-kb` (full re-index) and `GET /search?q=` (direct
  semantic search).

### Frontend enhancements
* Richer status cards: active model name, document/chunk counts, vector store in
  use, hover elevation.
* Inline explanations for DEMO MODE and unreachable backend, with the exact
  command needed to fix it.
* New design-system utilities (relevance score bars, chips) and cached network
  calls for instant page switching.

> `faiss-cpu` is optional — the RAG pipeline falls back to an exact numpy
> cosine search with identical scoring when FAISS is not installed.
