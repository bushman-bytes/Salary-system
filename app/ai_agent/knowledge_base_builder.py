"""
Knowledge Base Builder Module

This module builds and maintains the knowledge base by:
1. Loading documents from database
2. Generating embeddings
3. Storing in vector database
4. Managing updates and refreshes
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from langchain_core.documents import Document

from app.ai_agent.document_loader import DocumentLoader
from app.ai_agent.vector_store import get_vector_store
from app.ai_agent.config import CHROMA_COLLECTION_NAME, AI_PROVIDER


class KnowledgeBaseBuilder:
    """Builds and maintains the knowledge base."""
    
    def __init__(self, db: Session):
        """Initialize knowledge base builder."""
        self.db = db
        self.document_loader = DocumentLoader(db)
        self.vector_store = get_vector_store()
    
    def build_knowledge_base(
        self,
        employee_limit: Optional[int] = None,
        clear_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Build the complete knowledge base.
        
        Args:
            employee_limit: Optional limit on employees to process
            clear_existing: Whether to clear existing collection first
            
        Returns:
            Dictionary with build statistics
        """
        print("=" * 60)
        print("Building Knowledge Base")
        print("=" * 60)
        print(f"AI Provider: {AI_PROVIDER}")
        print(f"Collection: {CHROMA_COLLECTION_NAME}")
        print()
        
        # Clear existing if requested
        if clear_existing:
            print("Clearing existing knowledge base...")
            # Note: ChromaDB doesn't have direct delete in LangChain
            # You may need to manually delete the collection or recreate it
        
        # Load all documents
        print("\nLoading documents from database...")
        documents = self.document_loader.load_all_documents(employee_limit=employee_limit)
        
        if not documents:
            print("No documents found to add to knowledge base.")
            return {
                "status": "empty",
                "documents_loaded": 0,
                "documents_added": 0,
            }
        
        print(f"Loaded {len(documents)} documents")
        
        # Add documents to vector store
        print("\nAdding documents to vector store...")
        try:
            document_ids = self.vector_store.add_documents(documents)
            print(f"Successfully added {len(document_ids)} documents")
            
            # Count by type
            type_counts = {}
            for doc in documents:
                doc_type = doc.metadata.get("type", "unknown")
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            print("\nDocument breakdown by type:")
            for doc_type, count in type_counts.items():
                print(f"  - {doc_type}: {count}")
            
            return {
                "status": "success",
                "documents_loaded": len(documents),
                "documents_added": len(document_ids),
                "document_ids": document_ids[:10],  # First 10 IDs
                "type_counts": type_counts,
            }
        except Exception as e:
            print(f"Error adding documents: {e}")
            return {
                "status": "error",
                "error": str(e),
                "documents_loaded": len(documents),
                "documents_added": 0,
            }
    
    def add_domain_knowledge(self) -> Dict[str, Any]:
        """
        Add domain-specific knowledge documents.
        
        Returns:
            Dictionary with add statistics
        """
        domain_docs = self._create_domain_knowledge_documents()
        
        if not domain_docs:
            return {"status": "empty", "documents_added": 0}
        
        try:
            document_ids = self.vector_store.add_documents(domain_docs)
            return {
                "status": "success",
                "documents_added": len(document_ids),
                "document_ids": document_ids,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "documents_added": 0,
            }
    
    def _create_domain_knowledge_documents(self) -> List[Document]:
        """Create domain-specific knowledge documents."""
        documents = []
        
        # Salary Management System Overview
        doc = Document(
            page_content="""
Salary Management System - Overview

This system manages employee salaries, advance requests, bills, and attendance.

Key Features:
1. Advance Requests: Employees can request salary advances which require approval
2. Bill Management: Managers can record bills for employees
3. Role-Based Access: Staff, Manager, and Admin roles with different permissions
4. Attendance Tracking: Tracks days worked per month and total days worked

Workflow:
- Staff/Managers request advances → Admin approves/denies
- Managers record bills for staff → Bills are tracked per employee
- Attendance is tracked monthly and cumulatively

Key Terms:
- Advance: Pre-payment of salary before payday
- Bill: Expense recorded against an employee
- Status: pending, approved, or denied (for advances)
- Role: staff (basic), manager (can add bills), admin (full access)
""",
            metadata={
                "type": "domain_knowledge",
                "category": "system_overview",
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        documents.append(doc)
        
        # Advance Request Guidelines
        doc = Document(
            page_content="""
Advance Request Guidelines

Employees can request salary advances with the following characteristics:
- Amount: Any amount up to their monthly salary
- Status: Starts as "pending", can be "approved" or "denied" by admin
- Reason: Optional text field explaining the advance request
- Approval: Only admins can approve or deny advance requests

Common Patterns:
- Monthly advance requests are common
- Average advance amounts vary by employee role and salary
- Approval rates depend on employee history and request amount
- Denied requests typically have notes explaining the denial

Best Practices:
- Review employee's advance history before approval
- Consider total advances vs salary ratio
- Check for pending advances before approving new ones
- Document approval/denial reasons in notes
""",
            metadata={
                "type": "domain_knowledge",
                "category": "advance_guidelines",
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        documents.append(doc)
        
        # Bill Management Guidelines
        doc = Document(
            page_content="""
Bill Management Guidelines

Managers and Admins can record bills for employees:
- Bills are expenses charged to an employee
- Recorded by: Manager or Admin who creates the bill
- Billed to: Employee who the bill is for
- Amount: The bill amount
- Date: When the bill was incurred
- Reason: Optional explanation of the bill

Bill Tracking:
- Bills are tracked separately from advances
- Total bills per employee can be viewed
- Bills affect net salary calculations
- Historical bills are maintained for reporting

Best Practices:
- Record bills promptly after they occur
- Include clear reasons for bill recording
- Review bill patterns for unusual activity
- Bills should be legitimate business expenses
""",
            metadata={
                "type": "domain_knowledge",
                "category": "bill_guidelines",
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        documents.append(doc)
        
        # Report Generation Guidelines
        doc = Document(
            page_content="""
Report Generation Guidelines

The system generates various types of reports:

1. Employee Summary Reports:
   - Include advance request history
   - Show bill records
   - Display attendance information
   - Provide financial overview

2. Financial Reports:
   - Total advances requested vs approved
   - Total bills recorded
   - Monthly trends and patterns
   - Approval rates and statistics

3. Pattern Analysis:
   - Identify common advance request patterns
   - Analyze financial trends over time
   - Detect anomalies or unusual activity
   - Provide insights and recommendations

Report Best Practices:
- Include specific numbers and statistics
- Highlight trends and patterns
- Identify anomalies or concerns
- Provide actionable recommendations
- Use professional business language
""",
            metadata={
                "type": "domain_knowledge",
                "category": "report_guidelines",
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        documents.append(doc)
        
        return documents
    
    def refresh_knowledge_base(
        self,
        employee_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Refresh the knowledge base with latest data.
        
        Args:
            employee_limit: Optional limit on employees to process
            
        Returns:
            Dictionary with refresh statistics
        """
        print("Refreshing knowledge base...")
        return self.build_knowledge_base(
            employee_limit=employee_limit,
            clear_existing=False  # Add new documents, don't clear
        )
