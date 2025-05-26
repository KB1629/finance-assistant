"""Vector store implementation using FAISS and sentence-transformers."""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union
import numpy as np
import pandas as pd
from tqdm import tqdm

from sentence_transformers import SentenceTransformer
import faiss

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("retriever.vector_store")

# Default paths
DEFAULT_INDEX_DIR = Path("./cache/vector_store")
DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # Good balance of speed/quality
DEFAULT_INDEX_NAME = "finance_docs"

class FAISSVectorStore:
    """FAISS vector store for document retrieval."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        index_path: Optional[Path] = None,
        index_name: str = DEFAULT_INDEX_NAME
    ):
        """Initialize the vector store.
        
        Args:
            model_name: Name of the sentence-transformer model to use
            index_path: Path to save/load the index
            index_name: Name of the index
        """
        self.model_name = model_name
        self.index_name = index_name
        
        # Create index directory if it doesn't exist
        self.index_path = index_path or DEFAULT_INDEX_DIR
        os.makedirs(self.index_path, exist_ok=True)
        
        # Initialize model
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.vector_size = self.model.get_sentence_embedding_dimension()
        
        # Initialize index
        self.index = None
        self.document_lookup = {}
        self.document_ids = []
        
        # Try to load existing index
        self._load_or_create_index()

    def _get_index_files(self) -> Tuple[Path, Path]:
        """Get paths to index files.
        
        Returns:
            Tuple of (index_file, metadata_file)
        """
        index_file = self.index_path / f"{self.index_name}.faiss"
        metadata_file = self.index_path / f"{self.index_name}_metadata.json"
        return index_file, metadata_file

    def _load_or_create_index(self) -> None:
        """Load existing index or create a new one."""
        index_file, metadata_file = self._get_index_files()
        
        if index_file.exists() and metadata_file.exists():
            logger.info(f"Loading existing index from {index_file}")
            try:
                # Load FAISS index
                self.index = faiss.read_index(str(index_file))
                
                # Load document metadata
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    self.document_lookup = metadata["document_lookup"]
                    self.document_ids = metadata["document_ids"]
                    
                logger.info(f"Loaded index with {len(self.document_ids)} documents")
                return
            except Exception as e:
                logger.error(f"Failed to load index: {e}")
                logger.info("Creating new index")
        
        # Create new index if loading failed or files don't exist
        logger.info("Creating new FAISS index")
        self.index = faiss.IndexFlatIP(self.vector_size)  # Inner product index for cosine similarity
        self.document_lookup = {}
        self.document_ids = []

    def save(self) -> None:
        """Save the index and metadata to disk."""
        if self.index is None or len(self.document_ids) == 0:
            logger.warning("No documents indexed, skipping save")
            return
            
        index_file, metadata_file = self._get_index_files()
        
        # Save FAISS index
        logger.info(f"Saving index to {index_file}")
        faiss.write_index(self.index, str(index_file))
        
        # Save document metadata
        metadata = {
            "document_lookup": self.document_lookup,
            "document_ids": self.document_ids,
            "model_name": self.model_name,
            "vector_size": self.vector_size,
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
            
        logger.info(f"Saved index with {len(self.document_ids)} documents")

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        text_field: str = "text",
        batch_size: int = 32,
        show_progress: bool = True
    ) -> None:
        """Add documents to the vector store.
        
        Args:
            documents: List of document dictionaries
            text_field: Field in the document that contains the text to embed
            batch_size: Number of documents to embed at once
            show_progress: Whether to show progress bar
        """
        if not documents:
            logger.warning("No documents to add")
            return
            
        logger.info(f"Adding {len(documents)} documents to index")
        
        # Process documents in batches to avoid OOM issues
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            
            # Extract text and create ID mapping
            texts = []
            doc_map = {}
            
            for doc in batch:
                if text_field not in doc:
                    logger.warning(f"Document missing '{text_field}' field, skipping")
                    continue
                    
                # Generate document ID
                doc_id = len(self.document_ids) + len(doc_map)
                
                # Store text for embedding
                texts.append(doc[text_field])
                
                # Store document mapping
                doc_map[doc_id] = doc
            
            # Compute embeddings
            embeddings = self.model.encode(texts, show_progress_bar=show_progress)
            
            # Add vectors to FAISS index
            if len(embeddings) > 0:
                faiss.normalize_L2(embeddings)  # Normalize for cosine similarity
                self.index.add(embeddings)
                
                # Update document lookup and IDs
                self.document_lookup.update(doc_map)
                self.document_ids.extend(list(doc_map.keys()))
                
        logger.info(f"Total documents in index: {len(self.document_ids)}")
        
        # Save updated index
        self.save()

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 32,
        show_progress: bool = True
    ) -> None:
        """Add texts to the vector store.
        
        Args:
            texts: List of text strings
            metadatas: Optional list of metadata dictionaries
            batch_size: Number of texts to embed at once
            show_progress: Whether to show progress bar
        """
        if not texts:
            logger.warning("No texts to add")
            return
            
        # Convert texts to documents
        documents = []
        for i, text in enumerate(texts):
            doc = {"text": text}
            if metadatas and i < len(metadatas):
                doc.update(metadatas[i])
            documents.append(doc)
            
        self.add_documents(documents, batch_size=batch_size, show_progress=show_progress)

    def query(
        self,
        query_text: str,
        k: int = 5,
        threshold: Optional[float] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Query the vector store for similar documents.
        
        Args:
            query_text: Query text
            k: Number of results to return
            threshold: Optional similarity threshold (0-1)
            
        Returns:
            List of (document, score) tuples
        """
        if not query_text or self.index is None or self.index.ntotal == 0:
            logger.warning("Empty query or index, returning empty results")
            return []
            
        # Encode query
        query_embedding = self.model.encode([query_text])[0]
        
        # Normalize query embedding for cosine similarity
        faiss.normalize_L2(query_embedding.reshape(1, -1))
        
        # Search index
        k = min(k, self.index.ntotal)  # Don't request more results than we have
        scores, indices = self.index.search(query_embedding.reshape(1, -1), k)
        
        # Format results
        results = []
        for i, idx in enumerate(indices[0]):
            score = scores[0][i]
            
            # Apply threshold if specified
            if threshold is not None and score < threshold:
                continue
                
            # Get document
            idx_int = int(idx)
            if idx_int in self.document_lookup:
                results.append((self.document_lookup[idx_int], float(score)))
                
        return results

    def query_with_transformations(
        self,
        query_text: str,
        k: int = 5,
        prefix: str = "",
        suffix: str = "",
        threshold: Optional[float] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Query with optional text transformations.
        
        Args:
            query_text: Query text
            k: Number of results to return
            prefix: Optional prefix to add to query
            suffix: Optional suffix to add to query
            threshold: Optional similarity threshold (0-1)
            
        Returns:
            List of (document, score) tuples
        """
        transformed_query = f"{prefix}{query_text}{suffix}".strip()
        return self.query(transformed_query, k, threshold)

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store.
        
        Returns:
            Dictionary of statistics
        """
        return {
            "total_documents": len(self.document_ids),
            "index_size": self.index.ntotal if self.index else 0,
            "vector_dimension": self.vector_size,
            "model_name": self.model_name
        }


# Create global instance
_vector_store = None

def get_vector_store() -> FAISSVectorStore:
    """Get the global vector store instance.
    
    Returns:
        FAISSVectorStore instance
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = FAISSVectorStore()
    return _vector_store

def query(text: str, k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
    """Query the vector store for similar documents.
    
    Args:
        text: Query text
        k: Number of results to return
        
    Returns:
        List of (document, score) tuples
    """
    return get_vector_store().query(text, k)

def add_documents(documents: List[Dict[str, Any]], text_field: str = "text") -> None:
    """Add documents to the vector store.
    
    Args:
        documents: List of document dictionaries
        text_field: Field in the document that contains the text to embed
    """
    get_vector_store().add_documents(documents, text_field)

def add_texts(texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
    """Add texts to the vector store.
    
    Args:
        texts: List of text strings
        metadatas: Optional list of metadata dictionaries
    """
    get_vector_store().add_texts(texts, metadatas) 