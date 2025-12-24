"""
Query Processor Module

This module handles processing of database queries and preparing
data for AI agent processing.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.models.schema import Employee, Bill, Advance


class QueryProcessor:
    """Processes database queries for AI agent."""
    
    def __init__(self, db: Session):
        """Initialize query processor with database session."""
        self.db = db
    
    def get_employee_data(
        self,
        employee_id: Optional[int] = None,
        employee_name: Optional[str] = None,
        date_range: Optional[tuple[date, date]] = None,
    ) -> Dict[str, Any]:
        """
        Get employee data including advances, bills, and attendance.
        
        Args:
            employee_id: Employee ID
            employee_name: Employee name (first or last)
            date_range: Optional tuple of (start_date, end_date)
            
        Returns:
            Dictionary with employee data
        """
        # Query employee
        if employee_id:
            employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        elif employee_name:
            employee = self.db.query(Employee).filter(
                (Employee.first_name.ilike(f"%{employee_name}%")) |
                (Employee.last_name.ilike(f"%{employee_name}%"))
            ).first()
        else:
            return {"error": "Either employee_id or employee_name must be provided"}
        
        if not employee:
            return {"error": "Employee not found"}
        
        # Build query filters
        advance_filters = [Advance.employee_id == employee.id]
        bill_filters = [Bill.billed_employee_id == employee.id]
        
        if date_range:
            start_date, end_date = date_range
            # Advance uses created_at for date filtering
            advance_filters.append(Advance.created_at >= datetime.combine(start_date, datetime.min.time()))
            advance_filters.append(Advance.created_at <= datetime.combine(end_date, datetime.max.time()))
            # Bill uses date field
            bill_filters.append(Bill.date >= datetime.combine(start_date, datetime.min.time()))
            bill_filters.append(Bill.date <= datetime.combine(end_date, datetime.max.time()))
        
        # Get advances
        advances = self.db.query(Advance).filter(*advance_filters).all()
        
        # Get bills
        bills = self.db.query(Bill).filter(*bill_filters).all()
        
        # Format data
        return {
            "employee": {
                "id": employee.id,
                "first_name": employee.first_name,
                "last_name": employee.last_name,
                "role": employee.role.value if hasattr(employee.role, 'value') else str(employee.role),
                "salary": float(employee.salary) if employee.salary else None,
            },
            "advances": [
                {
                    "id": adv.id,
                    "amount": float(adv.amount_for_advance),
                    "date": adv.created_at.isoformat() if adv.created_at else None,
                    "status": adv.status.value if hasattr(adv.status, 'value') else str(adv.status),
                    "reason": adv.reason,
                }
                for adv in advances
            ],
            "bills": [
                {
                    "id": bill.id,
                    "amount": float(bill.amount_billed),
                    "date": bill.date.isoformat() if bill.date else None,
                    "reason": bill.reason,
                }
                for bill in bills
            ],
            "statistics": {
                "total_advances": len(advances),
                "total_advance_amount": sum(float(adv.amount_for_advance) for adv in advances),
                "pending_advances": len([a for a in advances if a.status.value == "pending"]),
                "approved_advances": len([a for a in advances if a.status.value == "approved"]),
                "total_bills": len(bills),
                "total_bill_amount": sum(float(bill.amount_billed) for bill in bills),
            }
        }
    
    def get_financial_data(
        self,
        date_range: Optional[tuple[date, date]] = None,
        employee_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get financial data for reporting.
        
        Args:
            date_range: Optional tuple of (start_date, end_date)
            employee_id: Optional employee ID to filter
            
        Returns:
            Dictionary with financial data
        """
        # Build query filters
        advance_filters = []
        bill_filters = []
        
        if date_range:
            start_date, end_date = date_range
            # Advance uses created_at for date filtering
            advance_filters.append(Advance.created_at >= datetime.combine(start_date, datetime.min.time()))
            advance_filters.append(Advance.created_at <= datetime.combine(end_date, datetime.max.time()))
            # Bill uses date field
            bill_filters.append(Bill.date >= datetime.combine(start_date, datetime.min.time()))
            bill_filters.append(Bill.date <= datetime.combine(end_date, datetime.max.time()))
        
        if employee_id:
            advance_filters.append(Advance.employee_id == employee_id)
            bill_filters.append(Bill.billed_employee_id == employee_id)
        
        # Get advances
        advances = self.db.query(Advance).filter(*advance_filters).all() if advance_filters else self.db.query(Advance).all()
        
        # Get bills
        bills = self.db.query(Bill).filter(*bill_filters).all() if bill_filters else self.db.query(Bill).all()
        
        # Calculate statistics
        total_advances_requested = sum(float(adv.amount_for_advance) for adv in advances)
        total_advances_approved = sum(
            float(adv.amount_for_advance) for adv in advances
            if adv.status.value == "approved"
        )
        total_bills = sum(float(bill.amount_billed) for bill in bills)
        
        return {
            "advances": {
                "total_count": len(advances),
                "total_requested": total_advances_requested,
                "total_approved": total_advances_approved,
                "pending_count": len([a for a in advances if a.status.value == "pending"]),
                "by_status": {
                    "pending": len([a for a in advances if a.status.value == "pending"]),
                    "approved": len([a for a in advances if a.status.value == "approved"]),
                    "denied": len([a for a in advances if a.status.value == "denied"]),
                }
            },
            "bills": {
                "total_count": len(bills),
                "total_amount": total_bills,
            },
            "date_range": {
                "start": date_range[0].isoformat() if date_range else None,
                "end": date_range[1].isoformat() if date_range else None,
            }
        }
