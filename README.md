# Multi-Agent Finance Assistant

A voice-enabled "Morning Market Brief" assistant that delivers spoken market analysis via a Streamlit app, backed by a microservice mesh of specialized agents.

## Features

- **Voice Interface**: Speech-to-text and text-to-speech capabilities
- **Multi-Agent Architecture**: Specialized agents for different tasks
- **Real-time Market Data**: Integration with AlphaVantage API
- **Document Retrieval**: RAG-powered analysis of financial filings
- **Portfolio Analytics**: Risk exposure and earnings analysis
- **Microservices**: FastAPI-based service mesh

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Voice Agent   │    │  Language Agent │    │ Analytics Agent │
│  (Whisper/TTS)  │    │  (LangGraph)    │    │  (Portfolio)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Orchestrator   │
                    │   (FastAPI)     │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Agent     │    │ Retriever Agent │    │ Scraper Agent   │
│ (AlphaVantage)  │    │   (FAISS)       │    │  (SEC Filings)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry
- Docker & Docker Compose

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd finance_assistant
```

2. Install dependencies:
```bash
poetry install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run with Docker Compose:
```bash
docker-compose up --build
```

5. Access the Streamlit UI:
```
http://localhost:8501
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ALPHAVANTAGE_KEY` | AlphaVantage API key | `demo` |
| `OPENAI_API_KEY` | OpenAI API key (optional) | `sk-...` |
| `LLM_PROVIDER` | LLM provider | `openai` or `local` |
| `WHISPER_HOST` | Whisper service URL | `http://whisper:9000` |
| `PIPER_VOICE` | TTS voice model | `en_US-amy` |

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Quality

```bash
poetry run black .
poetry run ruff check .
```

### Pre-commit Hooks

```bash
poetry run pre-commit install
```

## API Endpoints

### Orchestrator (Port 8000)

- `POST /query` - Process text query
- `POST /voice/query` - Process voice query
- `GET /health` - Health check

### Individual Agents

- API Agent: Port 8001
- Scraper Agent: Port 8002  
- Retriever Agent: Port 8003
- Analytics Agent: Port 8004
- Language Agent: Port 8005
- Voice Agent: Port 8006

## Project Structure

```
├── data_ingestion/     # Raw data fetchers & loaders
├── agents/            # Specialized agent services
├── orchestrator/      # FastAPI gateway & routing
├── streamlit_app/     # UI + voice widgets
├── tests/            # Test suites
├── docker/           # Docker configuration
└── docs/             # Documentation
```

## License

MIT License - see LICENSE file for details. 