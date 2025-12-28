"""
AI Agent Configuration Module

This module handles all configuration for the AI agent including:
- LLM provider settings (OpenAI/Hugging Face)
- Vector database configuration (ChromaDB)
- RAG pipeline settings
- Model parameters
"""

import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv, find_dotenv

# Load environment variables
# Explicitly try multiple .env file locations
project_root = Path(__file__).parent.parent.parent
config_env_path = project_root / "app" / "config" / ".env"
root_env_path = project_root / ".env"

# Try to load from app/config/.env first (most specific)
if config_env_path.exists():
    load_dotenv(config_env_path, override=True)
# Then try root .env
elif root_env_path.exists():
    load_dotenv(root_env_path, override=True)
# Fallback to find_dotenv() which searches upward
else:
    env_path = find_dotenv()
    if env_path:
        load_dotenv(env_path, override=True)

# ============================================================================
# LLM Provider Configuration
# ============================================================================

# Provider selection: "openai" or "huggingface"
AI_PROVIDER: str = os.getenv("AI_PROVIDER", "openai").lower()

# OpenAI Configuration
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Using gpt-4o-mini for cost efficiency
OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# Hugging Face Configuration
HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
HUGGINGFACE_MODEL: str = os.getenv(
    "HUGGINGFACE_MODEL", 
    "mistralai/Mistral-7B-Instruct-v0.3"  # Works with Inference API
)
HUGGINGFACE_EMBEDDING_MODEL: str = os.getenv(
    "HUGGINGFACE_EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2"
)

# ============================================================================
# Vector Store Configuration (ChromaDB)
# ============================================================================

VECTOR_STORE_TYPE: str = os.getenv("VECTOR_STORE_TYPE", "chromadb")
VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "./vector_store")

# Collection name based on AI provider (different embedding dimensions)
# OpenAI embeddings: 1536 dimensions (text-embedding-3-small)
# Hugging Face embeddings: 384 dimensions (all-MiniLM-L6-v2)
BASE_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "salary_queries")

# Dynamically set collection name based on provider
if AI_PROVIDER == "huggingface":
    CHROMA_COLLECTION_NAME: str = f"{BASE_COLLECTION_NAME}_hugFace"
else:
    CHROMA_COLLECTION_NAME: str = BASE_COLLECTION_NAME

# ChromaDB Cloud Configuration (optional - for cloud-hosted ChromaDB)
CHROMA_CLOUD_MODE: str = os.getenv("CHROMA_CLOUD_MODE", "local").lower()  # "local" or "cloud"
CHROMA_CLOUD_HOST: str = os.getenv("CHROMA_CLOUD_HOST", "")  # e.g., "https://your-tenant.chromadb.cloud"
CHROMA_CLOUD_API_KEY: str = os.getenv("CHROMA_CLOUD_API_KEY", "")  # Your ChromaDB Cloud API key
CHROMA_CLOUD_TENANT: str = os.getenv("CHROMA_CLOUD_TENANT", "")  # Your tenant ID
CHROMA_CLOUD_DATABASE: str = os.getenv("CHROMA_CLOUD_DATABASE", "default")  # Database name in cloud

# ============================================================================
# RAG Configuration
# ============================================================================

# Number of top documents to retrieve
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))

# Similarity threshold for retrieval (0.0 to 1.0)
RAG_SIMILARITY_THRESHOLD: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7"))

# Enable hybrid search (semantic + keyword)
ENABLE_HYBRID_SEARCH: bool = os.getenv("ENABLE_HYBRID_SEARCH", "true").lower() == "true"

# ============================================================================
# Model Configuration
# ============================================================================

# Maximum tokens in response
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))

# Temperature for generation (0.0 = deterministic, 1.0 = creative)
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.3"))

# Top-p sampling
TOP_P: float = float(os.getenv("TOP_P", "0.9"))

# ============================================================================
# Validation
# ============================================================================

def validate_config() -> dict[str, str]:
    """
    Validate AI agent configuration and return any errors.
    
    Returns:
        dict: Dictionary with "errors" key containing list of error messages
    """
    errors = []
    
    # Validate provider selection
    if AI_PROVIDER not in ["openai", "huggingface"]:
        errors.append(f"Invalid AI_PROVIDER: {AI_PROVIDER}. Must be 'openai' or 'huggingface'")
    
    # Validate OpenAI configuration
    if AI_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when AI_PROVIDER is 'openai'")
    
    # Validate Hugging Face configuration
    if AI_PROVIDER == "huggingface":
        if not HUGGINGFACE_API_KEY:
            errors.append("HUGGINGFACE_API_KEY is required when AI_PROVIDER is 'huggingface'")
    
    # Validate ChromaDB Cloud configuration
    if CHROMA_CLOUD_MODE not in ["local", "cloud"]:
        errors.append(f"Invalid CHROMA_CLOUD_MODE: {CHROMA_CLOUD_MODE}. Must be 'local' or 'cloud'")
    elif CHROMA_CLOUD_MODE == "cloud":
        if not CHROMA_CLOUD_API_KEY:
            errors.append("CHROMA_CLOUD_API_KEY is required when CHROMA_CLOUD_MODE is 'cloud'")
    
    # Validate RAG settings
    if RAG_TOP_K < 1:
        errors.append("RAG_TOP_K must be at least 1")
    
    if not 0.0 <= RAG_SIMILARITY_THRESHOLD <= 1.0:
        errors.append("RAG_SIMILARITY_THRESHOLD must be between 0.0 and 1.0")
    
    if not 0.0 <= TEMPERATURE <= 2.0:
        errors.append("TEMPERATURE must be between 0.0 and 2.0")
    
    if not 0.0 <= TOP_P <= 1.0:
        errors.append("TOP_P must be between 0.0 and 1.0")
    
    return {"errors": errors}


def get_config_summary() -> dict:
    """
    Get a summary of the current AI agent configuration.
    
    Returns:
        dict: Configuration summary (without sensitive keys)
    """
    return {
        "ai_provider": AI_PROVIDER,
        "openai_model": OPENAI_MODEL if AI_PROVIDER == "openai" else None,
        "huggingface_model": HUGGINGFACE_MODEL if AI_PROVIDER == "huggingface" else None,
        "embedding_model": OPENAI_EMBEDDING_MODEL if AI_PROVIDER == "openai" else HUGGINGFACE_EMBEDDING_MODEL,
        "vector_store_type": VECTOR_STORE_TYPE,
        "chroma_cloud_mode": CHROMA_CLOUD_MODE,
        "vector_store_path": VECTOR_STORE_PATH if CHROMA_CLOUD_MODE == "local" else "cloud",
        "chroma_collection_name": CHROMA_COLLECTION_NAME,
        "rag_top_k": RAG_TOP_K,
        "rag_similarity_threshold": RAG_SIMILARITY_THRESHOLD,
        "enable_hybrid_search": ENABLE_HYBRID_SEARCH,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "openai_api_key_set": bool(OPENAI_API_KEY),
        "huggingface_api_key_set": bool(HUGGINGFACE_API_KEY),
        "chroma_cloud_api_key_set": bool(CHROMA_CLOUD_API_KEY) if CHROMA_CLOUD_MODE == "cloud" else None,
    }
