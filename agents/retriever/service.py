"""
Retriever Agent FastAPI Microservice
Handles FAISS/Pinecone embeddings and retrieval operations
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from .vector_store import query, add_texts, get_vector_store_stats
from .document_loader import load_ticker_filings, load_asian_tech_filings, load_from_text_files

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("retriever_agent")

app = FastAPI(
    title="Retriever Agent",
    description="Vector embeddings and retrieval microservice",
    version="1.0.0"
)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    vector_store_stats: Dict[str, Any]


class QueryRequest(BaseModel):
    """Vector search request"""
    query: str
    k: int = 5
    score_threshold: Optional[float] = 0.7
    filter_metadata: Optional[Dict[str, Any]] = {}


class QueryResponse(BaseModel):
    """Vector search response"""
    results: List[Dict[str, Any]]
    query: str
    total_results: int
    status: str


class IndexRequest(BaseModel):
    """Document indexing request"""
    source_type: str  # "ticker", "asian_tech", "text_files", "custom"
    ticker: Optional[str] = None
    count: Optional[int] = 10
    days_back: Optional[int] = 30
    directory: Optional[str] = None
    texts: Optional[List[str]] = []
    metadata: Optional[List[Dict[str, Any]]] = []


class IndexResponse(BaseModel):
    """Document indexing response"""
    documents_indexed: int
    processing_time: float
    status: str


class StatsResponse(BaseModel):
    """Vector store statistics response"""
    total_documents: int
    total_chunks: int
    index_size: str
    last_updated: str
    status: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with vector store stats"""
    try:
        stats = get_vector_store_stats()
        return HealthResponse(
            status="healthy",
            service="retriever_agent",
            version="1.0.0",
            vector_store_stats=stats
        )
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return HealthResponse(
            status="degraded",
            service="retriever_agent", 
            version="1.0.0",
            vector_store_stats={"error": str(e)}
        )


@app.post("/query", response_model=QueryResponse)
async def search_vectors(request: QueryRequest):
    """Search vector store for relevant documents"""
    try:
        # Perform vector search
        results = query(
            query_text=request.query,
            k=request.k,
            score_threshold=request.score_threshold,
            filter_metadata=request.filter_metadata
        )
        
        return QueryResponse(
            results=results,
            query=request.query,
            total_results=len(results),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")


@app.post("/index", response_model=IndexResponse)
async def index_documents(request: IndexRequest):
    """Index documents into vector store"""
    try:
        import time
        start_time = time.time()
        
        documents_indexed = 0
        
        if request.source_type == "ticker" and request.ticker:
            # Load and index ticker filings
            docs = load_ticker_filings(request.ticker, request.count or 10)
            if docs:
                texts = [doc["content"] for doc in docs]
                metadata = [{"source": "ticker", "ticker": request.ticker, **doc} for doc in docs]
                add_texts(texts, metadata)
                documents_indexed = len(docs)
                
        elif request.source_type == "asian_tech":
            # Load and index Asian tech filings
            docs = load_asian_tech_filings(request.days_back or 30)
            if docs:
                texts = [doc["content"] for doc in docs]
                metadata = [{"source": "asian_tech", **doc} for doc in docs]
                add_texts(texts, metadata)
                documents_indexed = len(docs)
                
        elif request.source_type == "text_files" and request.directory:
            # Load and index text files from directory
            docs = load_from_text_files(request.directory)
            if docs:
                texts = [doc["content"] for doc in docs]
                metadata = [{"source": "text_files", **doc} for doc in docs]
                add_texts(texts, metadata)
                documents_indexed = len(docs)
                
        elif request.source_type == "custom" and request.texts:
            # Index custom texts
            metadata = request.metadata or [{"source": "custom"} for _ in request.texts]
            add_texts(request.texts, metadata)
            documents_indexed = len(request.texts)
            
        else:
            raise ValueError(f"Invalid source_type or missing required parameters")
            
        processing_time = time.time() - start_time
        
        return IndexResponse(
            documents_indexed=documents_indexed,
            processing_time=processing_time,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Indexing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document indexing failed: {str(e)}")


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get vector store statistics"""
    try:
        stats = get_vector_store_stats()
        
        return StatsResponse(
            total_documents=stats.get("total_documents", 0),
            total_chunks=stats.get("total_chunks", 0),
            index_size=stats.get("index_size", "0 MB"),
            last_updated=stats.get("last_updated", "N/A"),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unable to get stats: {str(e)}")


@app.delete("/index")
async def clear_index():
    """Clear the vector store index"""
    try:
        # Implementation would depend on your vector store
        # For now, return a placeholder response
        return {"message": "Index clearing not implemented", "status": "warning"}
        
    except Exception as e:
        logger.error(f"Clear index error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Index clearing failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 