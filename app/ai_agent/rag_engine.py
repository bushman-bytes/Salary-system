"""
RAG (Retrieval Augmented Generation) Engine

This module implements the RAG pipeline for enriching queries
with relevant context from the vector store.
"""

from typing import List, Dict, Any, Optional, Set
from langchain_core.documents import Document

from app.ai_agent.vector_store import get_vector_store
from app.ai_agent.config import RAG_TOP_K, ENABLE_HYBRID_SEARCH, RAG_SIMILARITY_THRESHOLD


class RAGEngine:
    """RAG engine for retrieving and enriching context."""
    
    def __init__(self):
        """Initialize the RAG engine."""
        self.vector_store = get_vector_store()
    
    def expand_query(self, query: str) -> List[str]:
        """
        Expand query with synonyms and related terms for better retrieval.
        
        Args:
            query: Original query
            
        Returns:
            List of query variations
        """
        query_lower = query.lower()
        variations = [query]  # Always include original
        
        # Common synonyms and expansions
        expansions = {
            "employee": ["staff", "worker", "personnel", "team member"],
            "advance": ["advance request", "salary advance", "pre-payment", "early payment"],
            "bill": ["expense", "charge", "cost", "invoice"],
            "summary": ["overview", "report", "analysis", "summary"],
            "financial": ["money", "financial", "budget", "expenses", "revenue"],
            "report": ["summary", "analysis", "overview", "report"],
        }
        
        # Add variations based on keywords
        for keyword, synonyms in expansions.items():
            if keyword in query_lower:
                for synonym in synonyms:
                    variation = query.replace(keyword, synonym)
                    if variation not in variations:
                        variations.append(variation)
        
        return variations[:3]  # Limit to 3 variations
    
    def retrieve_context(
        self,
        query: str,
        k: int = RAG_TOP_K,
        filter: Optional[Dict[str, Any]] = None,
        use_query_expansion: bool = True,
    ) -> List[Document]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: User query
            k: Number of documents to retrieve
            filter: Optional metadata filter
            use_query_expansion: Whether to use query expansion
            
        Returns:
            List of relevant Document objects
        """
        if use_query_expansion and ENABLE_HYBRID_SEARCH:
            # Multi-query retrieval
            query_variations = self.expand_query(query)
            all_documents = []
            seen_ids = set()
            
            for q in query_variations:
                docs = self.vector_store.similarity_search(q, k=k, filter=filter)
                for doc in docs:
                    # Use content hash as ID to avoid duplicates
                    doc_id = hash(doc.page_content)
                    if doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        all_documents.append(doc)
            
            # Return top k unique documents
            return all_documents[:k]
        else:
            # Simple similarity search
            return self.vector_store.similarity_search(query, k=k, filter=filter)
    
    def retrieve_context_with_scores(
        self,
        query: str,
        k: int = RAG_TOP_K,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[tuple[Document, float]]:
        """
        Retrieve relevant context with similarity scores.
        
        Args:
            query: User query
            k: Number of documents to retrieve
            filter: Optional metadata filter
            
        Returns:
            List of tuples (Document, similarity_score)
        """
        return self.vector_store.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter,
        )
    
    def format_context(
        self,
        documents: List[Document],
        include_metadata: bool = True,
        max_length: Optional[int] = None
    ) -> str:
        """
        Format retrieved documents into a context string.
        
        Args:
            documents: List of Document objects
            include_metadata: Whether to include metadata in context
            max_length: Optional maximum length for context (truncates if needed)
            
        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant context found."
        
        context_parts = []
        total_length = 0
        
        for i, doc in enumerate(documents, 1):
            content = doc.page_content
            metadata = doc.metadata
            
            # Build context entry
            entry_parts = [f"[Context {i}]"]
            
            if include_metadata and metadata:
                # Include relevant metadata
                relevant_meta = {}
                if "type" in metadata:
                    relevant_meta["type"] = metadata["type"]
                if "employee_name" in metadata:
                    relevant_meta["employee"] = metadata["employee_name"]
                if "month" in metadata:
                    relevant_meta["period"] = metadata["month"]
                
                if relevant_meta:
                    entry_parts.append(f"Type: {relevant_meta.get('type', 'unknown')}")
                    if "employee" in relevant_meta:
                        entry_parts.append(f"Employee: {relevant_meta['employee']}")
                    if "period" in relevant_meta:
                        entry_parts.append(f"Period: {relevant_meta['period']}")
            
            entry_parts.append(f"Content: {content}")
            entry = "\n".join(entry_parts)
            
            # Check length limit
            if max_length and total_length + len(entry) > max_length:
                # Truncate this entry if needed
                remaining = max_length - total_length - len("\n[Truncated...]")
                if remaining > 100:  # Only truncate if we have meaningful space
                    entry = entry[:remaining] + "\n[Truncated...]"
                    context_parts.append(entry)
                break
            
            context_parts.append(entry)
            total_length += len(entry)
        
        return "\n\n".join(context_parts)
    
    def retrieve_by_type(
        self,
        query: str,
        doc_type: str,
        k: int = RAG_TOP_K
    ) -> List[Document]:
        """
        Retrieve context filtered by document type.
        
        Args:
            query: User query
            doc_type: Document type to filter by (e.g., "employee_summary", "financial_pattern")
            k: Number of documents to retrieve
            
        Returns:
            List of relevant Document objects of specified type
        """
        filter_dict = {"type": doc_type}
        return self.retrieve_context(query, k=k, filter=filter_dict)


# Global RAG engine instance
_rag_engine_instance: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """
    Get or create the global RAG engine instance.
    
    Returns:
        RAGEngine instance
    """
    global _rag_engine_instance
    if _rag_engine_instance is None:
        _rag_engine_instance = RAGEngine()
    return _rag_engine_instance
