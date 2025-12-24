"""
Embedding Generation Module

This module handles embedding generation for documents and queries
using the configured embedding model.
"""

from typing import List
from langchain_core.documents import Document

from app.ai_agent.llm_provider import get_embedding_model


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors
    """
    embedding_model = get_embedding_model()
    return embedding_model.embed_documents(texts)


def generate_query_embedding(query: str) -> List[float]:
    """
    Generate embedding for a single query.
    
    Args:
        query: Query text to embed
        
    Returns:
        Embedding vector
    """
    embedding_model = get_embedding_model()
    return embedding_model.embed_query(query)


def embed_documents(documents: List[Document]) -> List[Document]:
    """
    Add embeddings to a list of documents.
    
    Args:
        documents: List of Document objects
        
    Returns:
        List of Document objects with embeddings added
    """
    embedding_model = get_embedding_model()
    
    # Extract texts from documents
    texts = [doc.page_content for doc in documents]
    
    # Generate embeddings
    embeddings = embedding_model.embed_documents(texts)
    
    # Add embeddings to documents
    for doc, embedding in zip(documents, embeddings):
        doc.metadata["embedding"] = embedding
    
    return documents
