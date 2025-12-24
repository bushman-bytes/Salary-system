"""
Chain Orchestrator Module

This module orchestrates multiple chains for complex queries,
handling error recovery, retries, and fallback strategies.
"""

from typing import Dict, Any, Optional, Callable
from functools import wraps
import time
import logging

from app.ai_agent.chains import get_rag_chain, get_structured_chain, get_multi_step_chain
from app.ai_agent.llm_provider import get_llm
from app.ai_agent.rag_engine import get_rag_engine

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator for retrying chain invocations on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
                    else:
                        raise last_exception
            return None
        return wrapper
    return decorator


class ChainOrchestrator:
    """Orchestrates multiple chains for complex query processing."""
    
    def __init__(self):
        """Initialize chain orchestrator."""
        self.rag_chain = get_rag_chain()
        self.multi_step_chain = get_multi_step_chain()
        self.rag_engine = get_rag_engine()
    
    def process_query(
        self,
        query: str,
        use_structured_output: bool = False,
        use_multi_step: bool = False,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Process a query using appropriate chain strategy.
        
        Args:
            query: User query
            use_structured_output: Whether to use structured output
            use_multi_step: Whether to use multi-step reasoning
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with response and metadata
        """
        start_time = time.time()
        
        try:
            if use_multi_step:
                # Use multi-step reasoning for complex queries
                steps = kwargs.get("steps", [
                    "Analyze the query requirements",
                    "Retrieve relevant context",
                    "Process the data",
                    "Generate insights"
                ])
                result = self.multi_step_chain.invoke(query, steps=steps, **kwargs)
                return {
                    "response": result.get("final_answer", ""),
                    "steps": result,
                    "metadata": {
                        "strategy": "multi_step",
                        "execution_time": time.time() - start_time,
                    }
                }
            elif use_structured_output:
                # Use structured output chain
                output_model = kwargs.get("output_model")
                if output_model:
                    structured_chain = get_structured_chain(output_model)
                    context = kwargs.get("context")
                    result = structured_chain.invoke(
                        prompt=query,
                        context=context,
                        max_retries=2
                    )
                    return {
                        "response": result,
                        "metadata": {
                            "strategy": "structured",
                            "execution_time": time.time() - start_time,
                        }
                    }
            
            # Default: Use RAG chain
            context = kwargs.get("context")
            response = self.rag_chain.invoke(query, context=context, **kwargs)
            
            return {
                "response": response,
                "metadata": {
                    "strategy": "rag",
                    "execution_time": time.time() - start_time,
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": None,
                "error": str(e),
                "metadata": {
                    "strategy": "failed",
                    "execution_time": time.time() - start_time,
                }
            }
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def process_with_retry(
        self,
        query: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Process query with automatic retry on failure.
        
        Args:
            query: User query
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with response and metadata
        """
        return self.process_query(query, **kwargs)
    
    def process_with_fallback(
        self,
        query: str,
        primary_strategy: str = "structured",
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Process query with fallback strategy.
        
        Args:
            query: User query
            primary_strategy: Primary strategy to try ("structured", "multi_step", "rag")
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with response and metadata
        """
        strategies = {
            "structured": {"use_structured_output": True},
            "multi_step": {"use_multi_step": True},
            "rag": {}
        }
        
        # Try primary strategy
        try:
            result = self.process_query(
                query,
                **strategies.get(primary_strategy, {}),
                **kwargs
            )
            if result.get("response") and "error" not in result:
                return result
        except Exception as e:
            logger.warning(f"Primary strategy {primary_strategy} failed: {e}")
        
        # Fallback to RAG
        logger.info("Falling back to RAG strategy")
        return self.process_query(query, **kwargs)


def get_chain_orchestrator() -> ChainOrchestrator:
    """Get chain orchestrator instance."""
    return ChainOrchestrator()
