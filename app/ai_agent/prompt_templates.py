"""
Prompt Templates Module

This module contains prompt engineering templates for different
query types and use cases.
"""

from typing import Dict, Any, Optional
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate


# ============================================================================
# System Prompts
# ============================================================================

SYSTEM_PROMPT_BASE = """You are an AI assistant for a salary management system. 
Your role is to generate accurate, comprehensive summaries and reports based on database queries.

Guidelines:
- Always base your responses on the provided data
- Use professional business language
- Include specific numbers and statistics when available
- Highlight important insights and patterns
- Format output as structured JSON when requested
- Be concise but comprehensive
"""

# ============================================================================
# Employee Summary Prompt
# ============================================================================

EMPLOYEE_SUMMARY_TEMPLATE = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT_BASE),
    HumanMessagePromptTemplate.from_template("""
Generate a comprehensive summary for the following employee data.

Context from knowledge base:
{retrieved_context}

Employee Data:
{employee_data}

Query Parameters:
- Employee: {employee_name}
- Time Period: {date_range}
- Include: {include_fields}

Generate a summary that includes:
1. Overview of employee's role and status
2. Summary of advance requests (pending, approved, denied)
3. Summary of bills recorded
4. Attendance patterns (if available)
5. Key insights and recommendations

Format the output as structured JSON with the following keys:
- overview
- advance_requests_summary
- bills_summary
- attendance_summary
- insights
- recommendations
""")
])

# ============================================================================
# Financial Report Prompt
# ============================================================================

FINANCIAL_REPORT_TEMPLATE = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT_BASE),
    HumanMessagePromptTemplate.from_template("""
You are an AI assistant analyzing financial data for a salary management system.

Historical Patterns:
{retrieved_context}

Current Data:
{financial_data}

Date Range: {date_range}
Filters: {filters}

Generate a financial report covering:
1. Total advances requested vs approved
2. Total bills recorded
3. Trends and patterns over time
4. Anomalies or concerns
5. Projections and recommendations

Use professional business language and include specific numbers with context.
Format the output as structured JSON with the following keys:
- summary
- advances_analysis
- bills_analysis
- trends
- anomalies
- projections
- recommendations
""")
])

# ============================================================================
# General Query Prompt
# ============================================================================

GENERAL_QUERY_TEMPLATE = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT_BASE),
    HumanMessagePromptTemplate.from_template("""
Answer the following question based on the provided context and data.

Context from knowledge base:
{retrieved_context}

Query Data:
{query_data}

User Question: {user_question}

Provide a clear, accurate answer based on the data provided. If the data doesn't contain
enough information to answer the question, state that clearly.
""")
])

# ============================================================================
# Prompt Factory
# ============================================================================

PROMPT_TEMPLATES = {
    "employee_summary": EMPLOYEE_SUMMARY_TEMPLATE,
    "financial_report": FINANCIAL_REPORT_TEMPLATE,
    "general_query": GENERAL_QUERY_TEMPLATE,
}


def get_prompt_template(template_name: str) -> ChatPromptTemplate:
    """
    Get a prompt template by name.
    
    Args:
        template_name: Name of the template
        
    Returns:
        ChatPromptTemplate instance
        
    Raises:
        ValueError: If template name is not found
    """
    if template_name not in PROMPT_TEMPLATES:
        raise ValueError(
            f"Unknown template name: {template_name}. "
            f"Available templates: {list(PROMPT_TEMPLATES.keys())}"
        )
    
    return PROMPT_TEMPLATES[template_name]


def format_prompt(
    template_name: str,
    **kwargs: Any
) -> str:
    """
    Format a prompt template with provided variables.
    
    Args:
        template_name: Name of the template
        **kwargs: Variables to format into the template
        
    Returns:
        Formatted prompt string
    """
    template = get_prompt_template(template_name)
    return template.format_messages(**kwargs)
