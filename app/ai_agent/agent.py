"""
Main AI Agent Orchestrator

This module provides the main interface for the AI agent,
coordinating all components (RAG, LLM, query processing, report generation).
"""

from typing import Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session

from app.ai_agent.report_generator import ReportGenerator
from app.ai_agent.config import get_config_summary, validate_config


class AIAgent:
    """Main AI Agent orchestrator."""
    
    def __init__(self, db_session: Session):
        """
        Initialize AI Agent.
        
        Args:
            db_session: SQLAlchemy database session
        """
        # Validate configuration
        config_errors = validate_config()
        if config_errors["errors"]:
            raise ValueError(f"Configuration errors: {', '.join(config_errors['errors'])}")
        
        self.db_session = db_session
        self.report_generator = ReportGenerator(db_session)
    
    def generate_summary(
        self,
        query_type: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Generate a summary based on query type.
        
        Args:
            query_type: Type of summary ("employee_summary", "financial_report", etc.)
            **kwargs: Additional parameters for the query
            
        Returns:
            Dictionary with summary and metadata
        """
        if query_type == "employee_summary":
            return self.report_generator.generate_employee_summary(**kwargs)
        elif query_type == "financial_report":
            return self.report_generator.generate_financial_report(**kwargs)
        else:
            raise ValueError(f"Unknown query type: {query_type}")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current AI agent configuration (without sensitive keys).
        
        Returns:
            Configuration dictionary
        """
        return get_config_summary()


def get_ai_agent(db_session: Session) -> AIAgent:
    """
    Create and return an AI Agent instance.
    
    Args:
        db_session: SQLAlchemy database session
        
    Returns:
        AIAgent instance
    """
    return AIAgent(db_session)
