"""
Document Loader Module

This module extracts data from the database and converts it into
documents suitable for the knowledge base.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from langchain_core.documents import Document

from app.models.schema import Employee, Bill, Advance, OffDay


class DocumentLoader:
    """Loads and processes data from database into documents."""
    
    def __init__(self, db: Session):
        """Initialize document loader with database session."""
        self.db = db
    
    def load_employee_summaries(self, limit: Optional[int] = None) -> List[Document]:
        """
        Load employee data as documents for knowledge base.
        
        Args:
            limit: Optional limit on number of employees to process
            
        Returns:
            List of Document objects
        """
        documents = []
        
        # Query employees
        query = self.db.query(Employee)
        if limit:
            query = query.limit(limit)
        employees = query.all()
        
        for emp in employees:
            # Get related data
            advances = self.db.query(Advance).filter(Advance.employee_id == emp.id).all()
            bills = self.db.query(Bill).filter(Bill.billed_employee_id == emp.id).all()
            off_days = self.db.query(OffDay).filter(OffDay.employee_id == emp.id).all()
            
            # Calculate statistics
            total_advances = len(advances)
            total_advance_amount = sum(float(a.amount_for_advance) for a in advances)
            pending_advances = len([a for a in advances if a.status.value == "pending"])
            approved_advances = len([a for a in advances if a.status.value == "approved"])
            total_bills = len(bills)
            total_bill_amount = sum(float(b.amount_billed) for b in bills)
            
            # Create document content
            content = f"""
Employee Profile: {emp.first_name} {emp.last_name}
Role: {emp.role.value}
Salary: ${emp.salary:,.2f}
Employment Start Date: {emp.employment_start_date}
Days Worked This Month: {emp.days_worked_this_month or 0}
Total Days Worked: {emp.total_days_worked or 0}

Advance Requests Summary:
- Total Advances: {total_advances}
- Total Amount Requested: ${total_advance_amount:,.2f}
- Pending: {pending_advances}
- Approved: {approved_advances}
- Denied: {total_advances - pending_advances - approved_advances}

Recent Advance Requests:
"""
            # Add recent advances
            for adv in sorted(advances, key=lambda x: x.created_at, reverse=True)[:5]:
                content += f"- {adv.created_at.strftime('%Y-%m-%d')}: ${adv.amount_for_advance:,.2f} ({adv.status.value})"
                if adv.reason:
                    content += f" - {adv.reason[:50]}"
                content += "\n"
            
            content += f"\nBills Summary:\n"
            content += f"- Total Bills: {total_bills}\n"
            content += f"- Total Amount: ${total_bill_amount:,.2f}\n"
            
            # Add recent bills
            if bills:
                content += "\nRecent Bills:\n"
                for bill in sorted(bills, key=lambda x: x.date, reverse=True)[:5]:
                    content += f"- {bill.date.strftime('%Y-%m-%d')}: ${bill.amount_billed:,.2f}"
                    if bill.reason:
                        content += f" - {bill.reason[:50]}"
                    content += "\n"
            
            # Create document with metadata
            doc = Document(
                page_content=content.strip(),
                metadata={
                    "type": "employee_summary",
                    "employee_id": emp.id,
                    "employee_name": f"{emp.first_name} {emp.last_name}",
                    "role": emp.role.value,
                    "created_at": datetime.utcnow().isoformat(),
                    "total_advances": total_advances,
                    "total_bills": total_bills,
                }
            )
            documents.append(doc)
        
        return documents
    
    def load_financial_patterns(self, months: int = 12) -> List[Document]:
        """
        Load financial patterns and trends as documents.
        
        Args:
            months: Number of months of historical data to analyze
            
        Returns:
            List of Document objects
        """
        documents = []
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=months * 30)
        
        # Get all advances in period
        advances = self.db.query(Advance).filter(
            Advance.created_at >= start_date
        ).all()
        
        # Get all bills in period
        bills = self.db.query(Bill).filter(
            Bill.date >= start_date
        ).all()
        
        # Calculate monthly patterns
        monthly_data = {}
        for adv in advances:
            month_key = adv.created_at.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"advances": [], "bills": []}
            monthly_data[month_key]["advances"].append(adv)
        
        for bill in bills:
            month_key = bill.date.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"advances": [], "bills": []}
            monthly_data[month_key]["bills"].append(bill)
        
        # Create document for each month
        for month, data in sorted(monthly_data.items()):
            total_advances = len(data["advances"])
            total_advance_amount = sum(float(a.amount_for_advance) for a in data["advances"])
            approved_amount = sum(
                float(a.amount_for_advance) for a in data["advances"]
                if a.status.value == "approved"
            )
            total_bills = len(data["bills"])
            total_bill_amount = sum(float(b.amount_billed) for b in data["bills"])
            
            content = f"""
Financial Summary for {month}:
- Total Advance Requests: {total_advances}
- Total Advance Amount Requested: ${total_advance_amount:,.2f}
- Total Advance Amount Approved: ${approved_amount:,.2f}
- Approval Rate: {(approved_amount / total_advance_amount * 100) if total_advance_amount > 0 else 0:.1f}%
- Total Bills: {total_bills}
- Total Bill Amount: ${total_bill_amount:,.2f}
- Net Financial Impact: ${(approved_amount + total_bill_amount):,.2f}
"""
            
            doc = Document(
                page_content=content.strip(),
                metadata={
                    "type": "financial_pattern",
                    "month": month,
                    "date": f"{month}-01",
                    "total_advances": total_advances,
                    "total_bills": total_bills,
                    "created_at": datetime.utcnow().isoformat(),
                }
            )
            documents.append(doc)
        
        # Create overall trend document
        if monthly_data:
            content = f"""
Financial Trends Analysis (Last {months} months):
- Average Monthly Advances: {sum(len(d['advances']) for d in monthly_data.values()) / len(monthly_data):.1f}
- Average Monthly Advance Amount: ${sum(sum(float(a.amount_for_advance) for a in d['advances']) for d in monthly_data.values()) / len(monthly_data):,.2f}
- Average Monthly Bills: {sum(len(d['bills']) for d in monthly_data.values()) / len(monthly_data):.1f}
- Average Monthly Bill Amount: ${sum(sum(float(b.amount_billed) for b in d['bills']) for d in monthly_data.values()) / len(monthly_data):,.2f}
"""
            doc = Document(
                page_content=content.strip(),
                metadata={
                    "type": "financial_trend",
                    "period_months": months,
                    "created_at": datetime.utcnow().isoformat(),
                }
            )
            documents.append(doc)
        
        return documents
    
    def load_advance_patterns(self) -> List[Document]:
        """
        Load advance request patterns and common reasons.
        
        Returns:
            List of Document objects
        """
        documents = []
        
        # Get all advances
        advances = self.db.query(Advance).all()
        
        if not advances:
            return documents
        
        # Analyze by status
        by_status = {}
        by_reason = {}
        
        for adv in advances:
            status = adv.status.value
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(adv)
            
            if adv.reason:
                reason_key = adv.reason.lower()[:50]  # Normalize reason
                if reason_key not in by_reason:
                    by_reason[reason_key] = []
                by_reason[reason_key].append(adv)
        
        # Create document for status patterns
        content = "Advance Request Status Patterns:\n"
        for status, adv_list in by_status.items():
            avg_amount = sum(float(a.amount_for_advance) for a in adv_list) / len(adv_list)
            content += f"- {status.capitalize()}: {len(adv_list)} requests, Average: ${avg_amount:,.2f}\n"
        
        doc = Document(
            page_content=content.strip(),
            metadata={
                "type": "advance_pattern",
                "pattern_category": "status",
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        documents.append(doc)
        
        # Create document for common reasons (top 10)
        if by_reason:
            sorted_reasons = sorted(by_reason.items(), key=lambda x: len(x[1]), reverse=True)[:10]
            content = "Common Advance Request Reasons:\n"
            for reason, adv_list in sorted_reasons:
                avg_amount = sum(float(a.amount_for_advance) for a in adv_list) / len(adv_list)
                content += f"- {reason}: {len(adv_list)} requests, Average: ${avg_amount:,.2f}\n"
            
            doc = Document(
                page_content=content.strip(),
                metadata={
                    "type": "advance_pattern",
                    "pattern_category": "reasons",
                    "created_at": datetime.utcnow().isoformat(),
                }
            )
            documents.append(doc)
        
        return documents
    
    def load_all_documents(self, employee_limit: Optional[int] = None) -> List[Document]:
        """
        Load all types of documents for knowledge base.
        
        Args:
            employee_limit: Optional limit on employees to process
            
        Returns:
            List of all Document objects
        """
        all_docs = []
        
        print("Loading employee summaries...")
        all_docs.extend(self.load_employee_summaries(limit=employee_limit))
        
        print("Loading financial patterns...")
        all_docs.extend(self.load_financial_patterns())
        
        print("Loading advance patterns...")
        all_docs.extend(self.load_advance_patterns())
        
        return all_docs
