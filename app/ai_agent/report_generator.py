"""
Report Generator Module

This module handles generation of AI-powered reports using
the LLM and RAG pipeline.
"""

from typing import Dict, Any, Optional, List
from datetime import date
from langchain_core.documents import Document

from app.ai_agent.llm_provider import get_llm
from app.ai_agent.rag_engine import get_rag_engine
from app.ai_agent.prompt_templates import get_prompt_template
from app.ai_agent.query_processor import QueryProcessor
from app.ai_agent.chains import (
    get_rag_chain,
    get_structured_chain,
    EmployeeSummaryOutput,
    FinancialReportOutput,
)
import time


class ReportGenerator:
    """Generates AI-powered reports."""
    
    def __init__(self, db_session):
        """Initialize report generator."""
        self.llm = get_llm()
        self.rag_engine = get_rag_engine()
        self.query_processor = QueryProcessor(db_session)
        self.rag_chain = get_rag_chain()
        self.employee_summary_chain = get_structured_chain(EmployeeSummaryOutput)
        self.financial_report_chain = get_structured_chain(FinancialReportOutput)
    
    def generate_employee_summary(
        self,
        employee_id: Optional[int] = None,
        employee_name: Optional[str] = None,
        date_range: Optional[tuple[date, date]] = None,
    ) -> Dict[str, Any]:
        """
        Generate AI-powered employee summary.
        
        Args:
            employee_id: Employee ID
            employee_name: Employee name
            date_range: Optional date range
            
        Returns:
            Dictionary with summary and metadata
        """
        # Get employee data
        employee_data = self.query_processor.get_employee_data(
            employee_id=employee_id,
            employee_name=employee_name,
            date_range=date_range,
        )
        
        if "error" in employee_data:
            return employee_data
        
        # Retrieve relevant context
        query = f"employee {employee_data['employee']['first_name']} {employee_data['employee']['last_name']} summary"
        context_docs = self.rag_engine.retrieve_context(query)
        retrieved_context = self.rag_engine.format_context(context_docs)
        
        # Format employee data as string
        import json
        employee_data_str = json.dumps(employee_data, indent=2)
        
        # Build prompt for structured output
        employee_name = f"{employee_data['employee']['first_name']} {employee_data['employee']['last_name']}"
        date_range_str = f"{date_range[0]} to {date_range[1]}" if date_range else "All time"
        
        prompt = f"""Generate a comprehensive employee summary based on the following data.

Context from knowledge base:
{retrieved_context}

Employee Data:
{employee_data_str}

Query Parameters:
- Employee: {employee_name}
- Time Period: {date_range_str}
- Include: advances, bills, attendance

Generate a summary that includes:
1. Overview of employee's role and status
2. Summary of advance requests (pending, approved, denied)
3. Summary of bills recorded
4. Attendance patterns (if available)
5. Key insights and recommendations
"""
        
        # Try structured output first, fallback to regular if it fails
        try:
            structured_result = self.employee_summary_chain.invoke(
                prompt=prompt,
                context=retrieved_context,
                max_retries=2
            )
            
            if "error" not in structured_result:
                return {
                    "summary": structured_result,
                    "data": employee_data,
                    "metadata": {
                        "query_type": "employee_summary",
                        "employee_id": employee_data['employee']['id'],
                        "date_range": date_range,
                        "format": "structured",
                    }
                }
        except Exception as e:
            # Fallback to regular RAG chain
            pass
        
        # Fallback: Use regular RAG chain
        summary_text = self.rag_chain.invoke(
            query=f"Generate employee summary for {employee_name}",
            context=retrieved_context,
            query_data=employee_data_str,
            employee_name=employee_name,
            date_range=date_range_str,
        )
        
        return {
            "summary": summary_text,
            "data": employee_data,
            "metadata": {
                "query_type": "employee_summary",
                "employee_id": employee_data['employee']['id'],
                "date_range": date_range,
                "format": "text",
            }
        }
    
    def generate_financial_report(
        self,
        date_range: Optional[tuple[date, date]] = None,
        employee_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate AI-powered financial report.
        
        Args:
            date_range: Optional date range
            employee_id: Optional employee ID to filter
            
        Returns:
            Dictionary with report and metadata
        """
        # Get financial data
        financial_data = self.query_processor.get_financial_data(
            date_range=date_range,
            employee_id=employee_id,
        )
        
        # Retrieve relevant context
        query = "financial report trends analysis"
        context_docs = self.rag_engine.retrieve_context(query)
        retrieved_context = self.rag_engine.format_context(context_docs)
        
        # Format financial data as string
        import json
        financial_data_str = json.dumps(financial_data, indent=2)
        
        # Build prompt for structured output
        date_range_str = f"{date_range[0]} to {date_range[1]}" if date_range else "All time"
        filters_str = f"Employee ID: {employee_id}" if employee_id else "All employees"
        
        prompt = f"""Generate a financial report based on the following data.

Historical Patterns:
{retrieved_context}

Current Data:
{financial_data_str}

Date Range: {date_range_str}
Filters: {filters_str}

Generate a financial report covering:
1. Total advances requested vs approved
2. Total bills recorded
3. Trends and patterns over time
4. Anomalies or concerns
5. Projections and recommendations
"""
        
        # Try structured output first, fallback to regular if it fails
        try:
            structured_result = self.financial_report_chain.invoke(
                prompt=prompt,
                context=retrieved_context,
                max_retries=2
            )
            
            if "error" not in structured_result:
                return {
                    "report": structured_result,
                    "data": financial_data,
                    "metadata": {
                        "query_type": "financial_report",
                        "date_range": date_range,
                        "employee_id": employee_id,
                        "format": "structured",
                    }
                }
        except Exception as e:
            # Fallback to regular RAG chain
            pass
        
        # Fallback: Use regular RAG chain
        report_text = self.rag_chain.invoke(
            query="Generate financial report with trends and analysis",
            context=retrieved_context,
            query_data=financial_data_str,
            date_range=date_range_str,
            filters=filters_str,
        )
        
        return {
            "report": report_text,
            "data": financial_data,
            "metadata": {
                "query_type": "financial_report",
                "date_range": date_range,
                "employee_id": employee_id,
                "format": "text",
            }
        }
