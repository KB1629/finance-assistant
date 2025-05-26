# Finance Assistant Architecture

## System Overview

The Finance Assistant is a multi-agent system designed to provide voice-enabled morning market briefs. The system is built using a microservices architecture with specialized agents for different functions.

## Sprint 2 - Intelligence Core Architecture

### Components Implemented

#### 1. Retriever Agent (`agents/retriever/`)
- **Purpose**: Vector-based document search and retrieval
- **Technology**: FAISS + sentence-transformers
- **Key Files**:
  - `vector_store.py`: FAISS vector store implementation
  - `document_loader.py`: Document processing and indexing
- **Capabilities**:
  - Semantic search over financial documents
  - SEC filing processing and chunking
  - Persistent vector index storage

#### 2. Analytics Agent (`agents/analytics/`)
- **Purpose**: Portfolio analysis and risk assessment
- **Technology**: Pandas + NumPy
- **Key Files**:
  - `portfolio.py`: Portfolio analytics engine
- **Capabilities**:
  - Portfolio value calculation
  - Geographic exposure analysis (Asia-Tech focus)
  - Earnings surprise detection
  - Risk exposure reporting

#### 3. Data Foundation (From Sprint 1)
- **API Agent**: AlphaVantage integration for market data
- **Scraper Agent**: SEC filing scraper for Asian tech companies

### Data Flow

```
Portfolio CSV → Analytics Agent → Market Data (API Agent)
                     ↓
            Geographic Analysis + Earnings Surprises
                     ↓
                 Risk Reports

SEC Filings → Document Loader → Vector Store → Retriever Agent
                                     ↓
                            Semantic Search Results
```

### Integration Points

1. **Portfolio Analysis**:
   - Input: `data/portfolio.csv` (symbol, shares, geo_tag)
   - Processing: Real-time price data + earnings analysis
   - Output: Risk exposure percentages and surprise alerts

2. **Document Retrieval**:
   - Input: Natural language queries
   - Processing: Vector similarity search
   - Output: Relevant document chunks with scores

### API Endpoints (Orchestrator)

- `POST /portfolio/value` - Get portfolio analytics
- `POST /portfolio/risk` - Get risk exposure analysis  
- `POST /retriever/query` - Query vector store
- `POST /retriever/index` - Index new documents

## Next Phase: Sprint 3

The next sprint will add:
- **Language Agent**: LangGraph + CrewAI workflow orchestration
- **Voice Agent**: Whisper STT + Piper TTS
- **Streamlit UI**: Voice-enabled frontend
- **Complete Microservices**: Docker containerization

## Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **Vector Store**: FAISS + sentence-transformers
- **Data Processing**: Pandas, NumPy
- **Testing**: pytest
- **Dependency Management**: Poetry
- **Data Sources**: AlphaVantage API, SEC filings 