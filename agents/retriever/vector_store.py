"""Vector store implementation using FAISS and sentence-transformers."""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Cache directory for models and index
CACHE_DIR = Path(__file__).parent.parent.parent / "cache"
VECTOR_STORE_DIR = CACHE_DIR / "vector_store"


class FAISSVectorStore:
    """FAISS vector store for document retrieval (with fallback for cloud deployment)."""
    
    def __init__(
        self,
        index_name: str = "finance_docs",
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        index_path: Optional[Path] = None
    ):
        self.index_name = index_name
        self.model_name = model_name
        self.index_path = index_path or VECTOR_STORE_DIR
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding model
        self.embedding_model = None
        self.index = None
        self.documents = []
        self.metadata = []
        self.vector_size = 384  # Default for all-MiniLM-L6-v2
        
        # Check if FAISS is available
        if not FAISS_AVAILABLE:
            logger.warning("FAISS not available - running in text-only mode")
            return
        
        self._load_embedding_model()
        self._load_or_create_index()
    
    def _load_embedding_model(self):
        """Load the sentence transformer model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.embedding_model = SentenceTransformer(self.model_name)
            logger.info(f"Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _load_or_create_index(self):
        """Load existing index or create a new one."""
        if not FAISS_AVAILABLE:
            logger.warning("FAISS not available - skipping index operations")
            return
            
        metadata_file = self.index_path / f"{self.index_name}_metadata.json"
        index_file = self.index_path / f"{self.index_name}.faiss"
        
        if index_file.exists() and metadata_file.exists():
            try:
                logger.info(f"Loading existing index from {index_file}")
                
                # Load metadata
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.documents = data.get('documents', [])
                    self.metadata = data.get('metadata', [])
                
                # Load FAISS index
                self.index = faiss.read_index(str(index_file))
                logger.info(f"Loaded index with {len(self.documents)} documents")
                
            except Exception as e:
                logger.error(f"Failed to load existing index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index."""
        if not FAISS_AVAILABLE:
            logger.warning("FAISS not available - cannot create index")
            return
            
        logger.info("Creating new FAISS index")
        self.index = faiss.IndexFlatIP(self.vector_size)  # Inner product index for cosine similarity
        self.documents = []
        self.metadata = []
        
        # Save empty index
        self._save_index()
    
    def _save_index(self):
        """Save the current index and metadata."""
        if not FAISS_AVAILABLE or self.index is None:
            logger.warning("FAISS not available or index not created - cannot save")
            return
            
        try:
            # Save FAISS index
            index_file = self.index_path / f"{self.index_name}.faiss"
            faiss.write_index(self.index, str(index_file))
            
            # Save metadata
            metadata_file = self.index_path / f"{self.index_name}_metadata.json"
            metadata = {
                'documents': self.documents,
                'metadata': self.metadata,
                'model_name': self.model_name,
                'vector_size': self.vector_size
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Index saved with {len(self.documents)} documents")
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            raise
    
    def add_documents(self, documents: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document texts
            metadata: Optional metadata for each document
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not FAISS_AVAILABLE:
            logger.warning("FAISS not available - cannot add documents")
            return False
            
        if not documents:
            return True
        
        if metadata is None:
            metadata = [{}] * len(documents)
        
        if len(documents) != len(metadata):
            raise ValueError("Number of documents must match number of metadata entries")
        
        try:
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(documents)} documents")
            embeddings = self.embedding_model.encode(documents, convert_to_numpy=True)
            
            # Ensure embeddings are float32
            embeddings = embeddings.astype(np.float32)
            
            # Add vectors to FAISS index
            if embeddings.ndim == 1:
                embeddings = embeddings.reshape(1, -1)
            faiss.normalize_L2(embeddings)  # Normalize for cosine similarity
            
            self.index.add(embeddings)
            
            # Store documents and metadata
            self.documents.extend(documents)
            self.metadata.extend(metadata)
            
            # Save updated index
            self._save_index()
            
            logger.info(f"Added {len(documents)} documents to index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    def query(
        self,
        query_text: str,
        k: int = 5,
        score_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Query the vector store for relevant documents.
        
        Args:
            query_text: Query string
            k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of documents with metadata and scores
        """
        if not FAISS_AVAILABLE:
            logger.warning("FAISS not available - returning empty results")
            return []
            
        if not self.documents or self.index is None:
            logger.warning("No documents in vector store or index not loaded")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query_text], convert_to_numpy=True)
            query_embedding = query_embedding.astype(np.float32)
            
            # Normalize query embedding
            faiss.normalize_L2(query_embedding.reshape(1, -1))
            
            # Search
            k = min(k, len(self.documents))  # Ensure k doesn't exceed available documents
            scores, indices = self.index.search(query_embedding, k)
            
            # Process results
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if score >= score_threshold and idx < len(self.documents):
                    result = {
                        'document': self.documents[idx],
                        'metadata': self.metadata[idx] if idx < len(self.metadata) else {},
                        'score': float(score),
                        'rank': i + 1
                    }
                    results.append(result)
            
            logger.info(f"Query returned {len(results)} results above threshold {score_threshold}")
            return results
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        if not FAISS_AVAILABLE:
            return {
                'total_documents': 0,
                'index_size': 0,
                'model_name': self.model_name,
                'faiss_available': False
            }
            
        return {
            'total_documents': len(self.documents),
            'index_size': self.index.ntotal if self.index else 0,
            'model_name': self.model_name,
            'vector_size': self.vector_size,
            'faiss_available': True
        }


# Global vector store instance
_vector_store: Optional[FAISSVectorStore] = None


def get_vector_store() -> FAISSVectorStore:
    """
    Get or create the global vector store instance.
    
    Returns:
        FAISSVectorStore instance
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = FAISSVectorStore()
    return _vector_store


def query(query_text: str, k: int = 5, score_threshold: float = 0.5) -> List[Dict[str, Any]]:
    """
    Query the vector store for relevant documents.
    
    Args:
        query_text: Query string
        k: Number of results to return  
        score_threshold: Minimum similarity score
        
    Returns:
        List of documents with metadata and scores
    """
    vector_store = get_vector_store()
    return vector_store.query(query_text, k, score_threshold)


def add_texts(texts: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> bool:
    """
    Add texts to the vector store.
    
    Args:
        texts: List of text documents
        metadata: Optional metadata for each document
        
    Returns:
        bool: True if successful, False otherwise
    """
    vector_store = get_vector_store()
    return vector_store.add_documents(texts, metadata) 