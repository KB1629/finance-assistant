"""Document loader for financial documents integration with vector store."""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
from datetime import datetime

from data_ingestion.scraper_agent.sec_scraper import SECFilingScraper, get_filings_for_ticker
from agents.retriever.vector_store import add_documents, add_texts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("retriever.document_loader")

# Default paths
DEFAULT_DOCS_DIR = Path("./cache/documents")

class DocumentLoader:
    """Document loader for processing and indexing financial documents."""

    def __init__(self, docs_dir: Optional[Path] = None):
        """Initialize the document loader.
        
        Args:
            docs_dir: Directory to store processed documents
        """
        self.docs_dir = docs_dir or DEFAULT_DOCS_DIR
        os.makedirs(self.docs_dir, exist_ok=True)
        
        # Initialize SEC scraper
        self.sec_scraper = SECFilingScraper()
    
    def process_sec_filing(self, filing: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process an SEC filing into indexable chunks.
        
        Args:
            filing: SEC filing dictionary
            
        Returns:
            List of document dictionaries
        """
        documents = []
        
        # Extract basic metadata
        metadata = {
            "source": "sec_filing",
            "company": filing.get("company", ""),
            "filing_type": filing.get("filing_type", ""),
            "filing_date": filing.get("filing_date", ""),
            "url": filing.get("url", ""),
            "processed_date": datetime.now().isoformat(),
        }
        
        # Process full text if available
        if "full_text" in filing and filing["full_text"]:
            # Split into manageable chunks (approx 1000 words each)
            text = filing["full_text"]
            chunks = self._split_text(text, max_length=1000)
            
            for i, chunk in enumerate(chunks):
                doc = {
                    "text": chunk,
                    "chunk_id": i,
                    **metadata
                }
                documents.append(doc)
        
        # Process sections if available
        if "sections" in filing and filing["sections"]:
            for section_name, section_text in filing["sections"].items():
                if not section_text:
                    continue
                    
                # For longer sections, split into chunks
                if len(section_text.split()) > 500:
                    chunks = self._split_text(section_text, max_length=500)
                    for i, chunk in enumerate(chunks):
                        doc = {
                            "text": chunk,
                            "section": section_name,
                            "chunk_id": i,
                            **metadata
                        }
                        documents.append(doc)
                else:
                    # Short section, keep as is
                    doc = {
                        "text": section_text,
                        "section": section_name,
                        **metadata
                    }
                    documents.append(doc)
        
        return documents
    
    def _split_text(self, text: str, max_length: int = 1000) -> List[str]:
        """Split text into chunks of approximately max_length words.
        
        Args:
            text: Text to split
            max_length: Maximum number of words per chunk
            
        Returns:
            List of text chunks
        """
        words = text.split()
        if len(words) <= max_length:
            return [text]
            
        chunks = []
        for i in range(0, len(words), max_length):
            chunk = ' '.join(words[i:i+max_length])
            chunks.append(chunk)
            
        return chunks
    
    def load_ticker_filings(self, ticker: str, count: int = 5) -> List[Dict[str, Any]]:
        """Load SEC filings for a ticker and convert to indexable documents.
        
        Args:
            ticker: Stock ticker symbol
            count: Number of filings to load
            
        Returns:
            List of document dictionaries
        """
        logger.info(f"Loading filings for {ticker}")
        
        try:
            # Get filings from SEC
            filings = get_filings_for_ticker(ticker, count)
            
            # Process each filing
            all_documents = []
            for filing in filings:
                documents = self.process_sec_filing(filing)
                all_documents.extend(documents)
                
                # Log progress
                logger.info(f"Processed {filing.get('filing_type', 'unknown')} filing for {filing.get('company', ticker)}")
                
            # Add to vector store
            if all_documents:
                logger.info(f"Adding {len(all_documents)} documents to vector store for {ticker}")
                add_documents(all_documents)
                
            return all_documents
        except Exception as e:
            logger.error(f"Error loading filings for {ticker}: {e}")
            return []
    
    def load_asian_tech_filings(self, days_back: int = 90) -> List[Dict[str, Any]]:
        """Load SEC filings for Asian tech companies.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of document dictionaries
        """
        logger.info(f"Loading Asian tech filings from past {days_back} days")
        
        try:
            # Get Asian tech tickers and filings
            asian_tech_tickers = [
                "TSM",   # Taiwan Semiconductor
                "BABA",  # Alibaba
                "9988.HK",  # Alibaba (Hong Kong)
                "BIDU",  # Baidu
                "SE",    # Sea Limited
                "GRAB",  # Grab
                "9618.HK",  # JD.com
                "BILI"   # Bilibili
            ]
            
            all_documents = []
            
            # Load filings for each ticker
            for ticker in asian_tech_tickers:
                documents = self.load_ticker_filings(ticker, count=3)
                all_documents.extend(documents)
                
            return all_documents
        except Exception as e:
            logger.error(f"Error loading Asian tech filings: {e}")
            return []
    
    def load_from_text_files(self, directory: Path) -> List[Dict[str, Any]]:
        """Load documents from text files in a directory.
        
        Args:
            directory: Directory containing text files
            
        Returns:
            List of document dictionaries
        """
        logger.info(f"Loading documents from {directory}")
        
        documents = []
        
        if not directory.exists() or not directory.is_dir():
            logger.error(f"Directory {directory} does not exist")
            return documents
            
        # Iterate through text files
        for file_path in directory.glob("*.txt"):
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    
                # Create document
                doc = {
                    "text": text,
                    "source": "file",
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                    "processed_date": datetime.now().isoformat()
                }
                
                documents.append(doc)
                logger.info(f"Loaded document from {file_path.name}")
                
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
                
        # Add to vector store
        if documents:
            logger.info(f"Adding {len(documents)} documents to vector store from files")
            add_documents(documents)
            
        return documents


# Module-level loader instance for easy access
_document_loader = None

def get_document_loader() -> DocumentLoader:
    """Get the global document loader instance.
    
    Returns:
        DocumentLoader instance
    """
    global _document_loader
    if _document_loader is None:
        _document_loader = DocumentLoader()
    return _document_loader

def load_ticker_filings(ticker: str, count: int = 5) -> List[Dict[str, Any]]:
    """Load SEC filings for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        count: Number of filings to load
        
    Returns:
        List of document dictionaries
    """
    return get_document_loader().load_ticker_filings(ticker, count)

def load_asian_tech_filings(days_back: int = 90) -> List[Dict[str, Any]]:
    """Load SEC filings for Asian tech companies.
    
    Args:
        days_back: Number of days to look back
        
    Returns:
        List of document dictionaries
    """
    return get_document_loader().load_asian_tech_filings(days_back)

def load_from_text_files(directory: str) -> List[Dict[str, Any]]:
    """Load documents from text files in a directory.
    
    Args:
        directory: Directory containing text files
        
    Returns:
        List of document dictionaries
    """
    return get_document_loader().load_from_text_files(Path(directory)) 