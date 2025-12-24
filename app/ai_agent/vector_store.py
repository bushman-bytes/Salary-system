"""
Vector Store Module

This module handles vector database operations using ChromaDB
for storing and retrieving document embeddings.
"""

import os
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

# Use langchain-chroma instead of deprecated langchain_community.vectorstores
try:
    from langchain_chroma import Chroma
except ImportError:
    # Fallback to old import if langchain-chroma not installed
    from langchain_community.vectorstores import Chroma

from app.ai_agent.config import (
    VECTOR_STORE_PATH,
    CHROMA_COLLECTION_NAME,
    RAG_TOP_K,
    RAG_SIMILARITY_THRESHOLD,
    CHROMA_CLOUD_MODE,
    CHROMA_CLOUD_HOST,
    CHROMA_CLOUD_API_KEY,
    CHROMA_CLOUD_TENANT,
    CHROMA_CLOUD_DATABASE,
)
from app.ai_agent.llm_provider import get_embedding_model


class VectorStore:
    """Wrapper class for vector store operations."""
    
    def __init__(self):
        """Initialize the vector store."""
        self.embedding_model = get_embedding_model()
        self.collection_name = CHROMA_COLLECTION_NAME
        self.cloud_mode = CHROMA_CLOUD_MODE == "cloud"
        
        # Initialize or load ChromaDB
        self._vector_store: Optional[Chroma] = None
        self._load_or_create_store()
    
    def _load_or_create_store(self):
        """Load existing vector store or create a new one."""
        if self.cloud_mode:
            # Try ChromaDB Cloud first
            try:
                self._load_cloud_store()
            except (ValueError, Exception) as e:
                # If cloud fails, fallback to local with warning
                import warnings
                warnings.warn(
                    f"ChromaDB Cloud connection failed: {e}\n"
                    "Falling back to local ChromaDB. Set CHROMA_CLOUD_MODE=local to avoid this warning.",
                    UserWarning
                )
                self.cloud_mode = False
                self._load_local_store()
        else:
            # Use local ChromaDB
            self._load_local_store()
    
    def _load_local_store(self):
        """Load or create local ChromaDB store."""
        self.vector_store_path = VECTOR_STORE_PATH
        
        # Ensure directory exists
        os.makedirs(self.vector_store_path, exist_ok=True)
        
        try:
            # Try to load existing store
            self._vector_store = Chroma(
                persist_directory=self.vector_store_path,
                embedding_function=self.embedding_model,
                collection_name=self.collection_name,
            )
        except Exception:
            # Create new store if loading fails
            self._vector_store = Chroma(
                persist_directory=self.vector_store_path,
                embedding_function=self.embedding_model,
                collection_name=self.collection_name,
            )
    
    def _load_cloud_store(self):
        """Load or create ChromaDB Cloud store."""
        if not CHROMA_CLOUD_API_KEY:
            raise ValueError(
                "CHROMA_CLOUD_API_KEY is required when CHROMA_CLOUD_MODE is 'cloud'. "
                "Please set it in your .env file."
            )
        
        # ChromaDB Cloud connection
        try:
            import chromadb
            
            # Use CloudClient for ChromaDB Cloud (recommended method)
            # CloudClient handles authentication and connection automatically
            client = chromadb.CloudClient(
                api_key=CHROMA_CLOUD_API_KEY,
                tenant=CHROMA_CLOUD_TENANT if CHROMA_CLOUD_TENANT else None,
                database=CHROMA_CLOUD_DATABASE if CHROMA_CLOUD_DATABASE else None,
            )
            
            # Create LangChain Chroma wrapper with cloud client
            # For cloud, we need to pass the client directly
            self._vector_store = Chroma(
                client=client,
                embedding_function=self.embedding_model,
                collection_name=self.collection_name,
            )
        except ImportError:
            raise ImportError(
                "chromadb package is required for cloud mode. "
                "Install it with: pip install chromadb"
            )
        except Exception as e:
            # If cloud connection fails, provide helpful error message
            error_msg = str(e)
            if "Permission denied" in error_msg or "401" in error_msg or "403" in error_msg:
                raise ValueError(
                    f"ChromaDB Cloud authentication failed: {error_msg}\n"
                    "Please verify:\n"
                    "1. CHROMA_CLOUD_API_KEY is correct\n"
                    "2. Your ChromaDB Cloud account is active\n"
                    "3. The API key has proper permissions"
                )
            else:
                raise ValueError(
                    f"Failed to connect to ChromaDB Cloud: {error_msg}. "
                    "Please check your CHROMA_CLOUD_API_KEY and CHROMA_CLOUD_HOST settings. "
                    "Make sure you have a valid ChromaDB Cloud account and API key."
                )
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of Document objects to add
            
        Returns:
            List of document IDs
        """
        if not self._vector_store:
            self._load_or_create_store()
        
        return self._vector_store.add_documents(documents)
    
    def similarity_search(
        self,
        query: str,
        k: int = RAG_TOP_K,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        Search for similar documents.
        
        Args:
            query: Query text
            k: Number of documents to retrieve
            filter: Optional metadata filter
            
        Returns:
            List of similar Document objects
        """
        if not self._vector_store:
            self._load_or_create_store()
        
        return self._vector_store.similarity_search(
            query=query,
            k=k,
            filter=filter,
        )
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = RAG_TOP_K,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[tuple[Document, float]]:
        """
        Search for similar documents with similarity scores.
        
        Args:
            query: Query text
            k: Number of documents to retrieve
            filter: Optional metadata filter
            
        Returns:
            List of tuples (Document, similarity_score)
        """
        if not self._vector_store:
            self._load_or_create_store()
        
        results = self._vector_store.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter,
        )
        
        # Filter by similarity threshold
        filtered_results = [
            (doc, score) for doc, score in results
            if score >= RAG_SIMILARITY_THRESHOLD
        ]
        
        return filtered_results
    
    def delete_collection(self):
        """Delete the entire collection (use with caution)."""
        if self._vector_store:
            # ChromaDB doesn't have a direct delete method in LangChain
            # This would require direct ChromaDB client access
            pass


# Global vector store instance
_vector_store_instance: Optional[VectorStore] = None
_current_collection_name: Optional[str] = None


def get_vector_store() -> VectorStore:
    """
    Get or create the global vector store instance.
    
    Automatically recreates the instance if the collection name changes
    (e.g., when switching between OpenAI and Hugging Face providers).
    
    Returns:
        VectorStore instance
    """
    global _vector_store_instance, _current_collection_name
    
    # Check if collection name has changed (provider switch)
    if _vector_store_instance is None or _current_collection_name != CHROMA_COLLECTION_NAME:
        _vector_store_instance = VectorStore()
        _current_collection_name = CHROMA_COLLECTION_NAME
    
    return _vector_store_instance
