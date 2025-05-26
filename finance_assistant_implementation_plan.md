# Multi‑Agent Finance Assistant — Implementation Blueprint  
*(Hand‑this file directly to Cursor or any coding‑agent to execute without guesswork)*  

## Project Overview  
Build a voice‑enabled “Morning Market Brief” assistant that runs as a Streamlit app and is backed by a micro‑service mesh of specialised agents (API, Scraper, Retriever, Analytics, Language, Voice).  
All components are open‑source, containerised, and wired together through FastAPI and WebSockets.  

---

## Repository Layout (do **not** modify)  

```text
/data_ingestion          # raw fetchers & loaders
/agents                  # API, Scraper, Retriever, Analytics, Language, Voice
/orchestrator            # FastAPI gateway & routing
/streamlit_app           # UI + voice widgets
/tests                   # pytest suites added each phase
/docker                  # Dockerfile(s) + docker-compose.yml
docs/
    architecture.md
    ai_tool_usage.md
```

*Python 3.11 · Poetry · FAISS · Whisper · Piper · CrewAI · LangGraph 0.4+*

---

## Sprint Plan & Quality Gates  

> **Timeline note** – three sprints fit comfortably into 26 → 29 May window  
> (≈ 3 × 1‑day sprints + buffer).  
> **Rule**: advance only when the sprint gate passes.  

| Sprint | Deliverables | Gate (run / manual) |
|--------|--------------|---------------------|
| **S‑0 Bootstrap (½ day)** | Repo skeleton, Poetry, pre‑commit, GitHub Actions CI (lint + `pytest -q`), docker‑compose stub with “hello‑world” FastAPI. | GH Actions ✅ green |
| **S‑1 Data Foundation (1 day)** | **API Agent** (`data_ingestion/api_agent/alphavantage_client.py`) + **Scraper Agent** using Sec‑API RSS; raw data cached. | `pytest tests/test_ingestion.py` verifies ≥1 JSON & ≥1 filing |
| **S‑2 Intelligence Core (1 day)** | **Retriever Agent** (FAISS + `sentence-transformers/gte-small`) + **Analytics Agent** (exposure %, earnings surprises) + unit tests. | `pytest tests/test_retriever.py` & `tests/test_analytics.py` |
| **S‑3 Conversation & Voice (1 day)** | **Language Agent** (LangGraph, LLM summary) · **Voice Agent** (Whisper STT docker wrapper + Piper TTS) · **Orchestrator** service mesh (7 FastAPI micro‑services) · **Streamlit UI** deployed. | `curl /orchestrator/query` returns JSON; Streamlit URL loads & plays audio |
| **S‑4 Docs & Hardening (buffer)** | `README.md`, `docs/architecture.md` diagram, `docs/ai_tool_usage.md` log export; test coverage ≥80 %. | GH Actions badge ✔ coverage badge ≥80 % |

---

### Detailed Task List per Sprint  

#### Sprint 0 – Bootstrap  
1. `poetry new finance_assistant` → create fixed folder contract.  
2. Add **pre‑commit** (black, ruff).  
3. GitHub Actions workflow: lint, `pytest`, `docker-compose up --build --exit-code-from orchestrator`.  

---

#### Sprint 1 – Data Foundation  
1. **API Agent**  
   * Use AlphaVantage (`TIME_SERIES_DAILY_ADJUSTED`, `EARNINGS`) endpoints.  
   * Expose:  
     ```python
     get_price(symbol:str, date:date)->float  
     get_earnings_surprise(symbol:str, period:str)->float  # % beat/miss
     ```  
2. **Scraper Agent**  
   * Ingest SEC 6‑K/20‑F Asian tech filings via Sec‑API RSS; fallback to simple `requests+BeautifulSoup`.  
   * Store raw HTML and cleaned text.  
3. Write `tests/test_ingestion.py` asserting non‑empty fetch.  

---

#### Sprint 2 – Intelligence Core  
1. **Retriever Agent**  
   * `agents/retriever/vector_store.py`: build FAISS index; expose `query(text,k)` returning `(doc, score)`.  
2. **Analytics Agent**  
   * Input: `portfolio.csv` (symbol, shares, geo_tag).  
   * Compute latest market value via API Agent; group by `Asia-Tech` tag → `% of AUM`.  
   * Flag earnings surprises: abs(% surprise) > 1 %.  
3. Unit tests for both agents.  
4. Update `docs/architecture.md` (sequence & data‑flow diagrams).  

---

#### Sprint 3 – Conversation, Voice & UI  
1. **Language Agent** (LangGraph + CrewAI)  
   * Nodes: Retriever → Analytics → LLM (GPT‑4o / Mistral‑7B).  
   * Prompt: deterministic summary ≤60 words.  
2. **Voice Agent**  
   * Whisper STT docker (`ghcr.io/openai/whisper`).  
   * Piper TTS CLI (EN‑US‑amy).  
   * Expose `/voice/stt`, `/voice/tts`.  
3. **Micro‑services** (FastAPI, Pydantic schemas) – one container per agent plus Redis.  
4. **Orchestrator** route: text/voice → agents → text → voice.  
5. **Streamlit UI**  
   * Mic button, text box, live token stream, audio playback, latency timer.  
   * Deployed to Streamlit Community Cloud (`streamlit_app/main.py`).  
6. Smoke test script `scripts/e2e_voice_demo.py` for CI.  

---

#### Sprint 4 – Docs, Tests, Release  
1. Finish `README.md` (setup, docker‑compose, env vars).  
2. Add AI‑tool logs (`docs/ai_tool_usage.md`) – export from Cursor session history.  
3. Draw.io PNG architecture diagram → `docs/img/architecture.png`.  
4. Increase test coverage ≥80 %, add load‑test (locust) optional.  
5. Tag `v1.0.0` GitHub release; optional 60‑sec Loom demo.  

---

## Environment Variables  

| Name | Example | Notes |
|------|---------|-------|
| `ALPHAVANTAGE_KEY` | `demo` | required |
| `LLM_PROVIDER` | `openai` \| `local` | choose model |
| `OPENAI_API_KEY` | … | if provider = openai |
| `WHISPER_HOST` | `http://whisper:9000` | docker‑compose service |
| `PIPER_VOICE` | `en_US-amy` | … |

---

## Command Quick‑ref  

```bash
# run complete stack locally
docker-compose up --build

# run unit tests
pytest -q

# query orchestrator (text)
curl -X POST localhost:8000/query -d '{"text": "Risk exposure in Asia tech today?"}'

# open Streamlit UI
streamlit run streamlit_app/main.py
```

---

## Definition of Done  
* All sprint gates pass.  
* Streamlit URL returns answer & audio within 3 s median latency.  
* GitHub repo public, Docker compose up, docs complete.  

---

*File generated 26 May 2025 17:30 IST*  
