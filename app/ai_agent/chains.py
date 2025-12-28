"""
LangChain Chains Module

This module implements LangChain chains for the RAG pipeline:
- RAG chains for query → context → LLM → response
- Structured output chains with JSON parsing
- Multi-step reasoning chains
"""

from typing import Dict, Any, Optional, List
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import json

from app.ai_agent.llm_provider import get_llm
from app.ai_agent.rag_engine import get_rag_engine
from app.ai_agent.vector_store import get_vector_store
from app.ai_agent.prompt_templates import get_prompt_template


# ============================================================================
# Structured Output Models
# ============================================================================

class EmployeeSummaryOutput(BaseModel):
    """Structured output for employee summary."""
    overview: str = Field(description="Overview of employee's role and status")
    advance_requests_summary: str = Field(description="Summary of advance requests")
    bills_summary: str = Field(description="Summary of bills recorded")
    attendance_summary: str = Field(description="Attendance patterns if available")
    insights: List[str] = Field(description="Key insights about the employee")
    recommendations: List[str] = Field(description="Recommendations for management")


class FinancialReportOutput(BaseModel):
    """Structured output for financial report."""
    summary: str = Field(description="Executive summary of financial data")
    advances_analysis: str = Field(description="Analysis of advance requests")
    bills_analysis: str = Field(description="Analysis of bills")
    trends: str = Field(description="Trends and patterns identified")
    anomalies: List[str] = Field(description="Anomalies or concerns detected")
    projections: str = Field(description="Future projections")
    recommendations: List[str] = Field(description="Actionable recommendations")


# ============================================================================
# RAG Chain
# ============================================================================

class RAGChain:
    """RAG chain for query → context retrieval → LLM → response."""
    
    def __init__(self):
        """Initialize RAG chain."""
        self.llm = get_llm()
        self.rag_engine = get_rag_engine()
        self.vector_store = get_vector_store()
    
    def invoke(
        self,
        query: str,
        context: Optional[str] = None,
        prompt_template: Optional[PromptTemplate] = None,
        **kwargs: Any
    ) -> str:
        """
        Invoke RAG chain with query.
        
        Args:
            query: User query
            context: Optional pre-retrieved context
            prompt_template: Optional custom prompt template
            **kwargs: Additional parameters for prompt
            
        Returns:
            LLM response as string
        """
        # Retrieve context if not provided
        if context is None:
            context_docs = self.rag_engine.retrieve_context(query)
            context = self.rag_engine.format_context(context_docs)
        
        # Use default prompt if not provided
        if prompt_template is None:
            from app.ai_agent.prompt_templates import GENERAL_QUERY_TEMPLATE
            prompt_template = GENERAL_QUERY_TEMPLATE
        
        # Extract query_data from kwargs to avoid duplicate keyword argument
        query_data = kwargs.pop("query_data", "")
        
        # Format prompt
        messages = prompt_template.format_messages(
            retrieved_context=context,
            query_data=query_data,
            user_question=query,
            **kwargs
        )
        
        # Invoke LLM
        try:
            # Try to invoke with messages (for chat models)
            response = self.llm.invoke(messages)
            
            # Handle different response types
            if hasattr(response, 'content'):
                return response.content
            elif isinstance(response, str):
                return response
            else:
                return str(response)
        except Exception as e:
            # If messages don't work, try converting to string prompt
            # This handles text generation models that don't support chat format
            try:
                # Convert messages to a single prompt string
                prompt_text = ""
                for msg in messages:
                    if hasattr(msg, 'content'):
                        prompt_text += f"{msg.content}\n\n"
                    else:
                        prompt_text += f"{str(msg)}\n\n"
                
                # Try invoking with string directly
                response = self.llm.invoke(prompt_text)
                return str(response)
            except Exception as e2:
                raise ValueError(
                    f"Failed to invoke LLM: {str(e)}. "
                    f"Fallback also failed: {str(e2)}"
                )


# ============================================================================
# Structured Output Chain
# ============================================================================

class StructuredOutputChain:
    """Chain for generating structured JSON output."""
    
    def __init__(self, output_model: BaseModel):
        """
        Initialize structured output chain.
        
        Args:
            output_model: Pydantic model for output structure
        """
        self.llm = get_llm()
        self.output_parser = PydanticOutputParser(pydantic_object=output_model)
        self.output_model = output_model
    
    def invoke(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Invoke chain with structured output parsing.
        
        Args:
            prompt: Input prompt
            context: Optional context to include
            max_retries: Maximum retry attempts for parsing
            
        Returns:
            Parsed structured output as dictionary
        """
        # Build full prompt with format instructions
        format_instructions = self.output_parser.get_format_instructions()
        
        full_prompt = f"""{prompt}

{format_instructions}
"""
        
        if context:
            full_prompt = f"""Context:
{context}

{prompt}

{format_instructions}
"""
        
        # Try to get structured output with retries
        response_text = None
        for attempt in range(max_retries):
            try:
                # Format as messages for chat models
                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content=full_prompt)]
                
                # Invoke LLM
                response = self.llm.invoke(messages)
                
                # Handle different response types
                if hasattr(response, 'content'):
                    response_text = response.content
                elif isinstance(response, str):
                    response_text = response
                else:
                    response_text = str(response)
                
                # Try to extract JSON from response if it's wrapped in markdown
                if "```json" in response_text:
                    import re
                    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)
                elif "```" in response_text:
                    # Try to extract code block content
                    import re
                    code_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
                    if code_match:
                        response_text = code_match.group(1)
                
                # Parse structured output
                parsed = self.output_parser.parse(response_text)
                return parsed.dict()
            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt failed, return raw response
                    return {
                        "error": f"Failed to parse structured output: {e}",
                        "raw_response": response_text
                    }
                continue
        
        return {"error": "Failed to generate structured output", "raw_response": response_text}


# ============================================================================
# Multi-Step Reasoning Chain
# ============================================================================

class MultiStepChain:
    """Chain for multi-step reasoning with intermediate steps."""
    
    def __init__(self):
        """Initialize multi-step chain."""
        self.llm = get_llm()
        self.rag_engine = get_rag_engine()
    
    def invoke(
        self,
        query: str,
        steps: List[str],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Invoke multi-step reasoning chain.
        
        Args:
            query: Initial query
            steps: List of step descriptions
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with results from each step
        """
        results = {}
        current_context = ""
        
        for i, step in enumerate(steps, 1):
            # Retrieve context for this step
            step_query = f"{query} {step}"
            context_docs = self.rag_engine.retrieve_context(step_query)
            step_context = self.rag_engine.format_context(context_docs)
            
            # Build prompt for this step
            step_prompt = f"""
Step {i}: {step}

Previous Context:
{current_context}

Current Context:
{step_context}

Query: {query}

Provide analysis for this step.
"""
            
            # Invoke LLM for this step
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content=step_prompt)]
            response = self.llm.invoke(messages)
            
            # Handle different response types
            if hasattr(response, 'content'):
                step_result = response.content
            elif isinstance(response, str):
                step_result = response
            else:
                step_result = str(response)
            
            results[f"step_{i}"] = {
                "step": step,
                "result": step_result,
                "context_used": step_context[:200] + "..." if len(step_context) > 200 else step_context
            }
            
            # Update context for next step
            current_context += f"\nStep {i} Result: {step_result}\n"
        
        # Final synthesis
        synthesis_prompt = f"""
Based on the following step-by-step analysis, provide a final comprehensive answer.

Query: {query}

Step Results:
{json.dumps(results, indent=2)}

Provide a synthesized final answer.
"""
        
        # Invoke LLM for final synthesis
        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content=synthesis_prompt)]
        final_response = self.llm.invoke(messages)
        
        # Handle different response types
        if hasattr(final_response, 'content'):
            results["final_answer"] = final_response.content
        elif isinstance(final_response, str):
            results["final_answer"] = final_response
        else:
            results["final_answer"] = str(final_response)
        
        return results


# ============================================================================
# Chain Factory
# ============================================================================

def get_rag_chain() -> RAGChain:
    """Get RAG chain instance."""
    return RAGChain()


def get_structured_chain(output_model: BaseModel) -> StructuredOutputChain:
    """Get structured output chain for a specific model."""
    return StructuredOutputChain(output_model)


def get_multi_step_chain() -> MultiStepChain:
    """Get multi-step reasoning chain."""
    return MultiStepChain()
