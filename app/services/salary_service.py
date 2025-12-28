"""
Service for handling monthly salary resets and used_salary management.
Handles carrying forward negative balances (debts) to the next month.
"""
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.schema import Employee, Bill, Advance, AdvanceStatus


def calculate_used_salary_from_transactions(db: Session, employee_id: int) -> float:
    """
    Calculate used salary from bills and approved advances for an employee.
    
    Args:
        db: Database session
        employee_id: Employee ID
    
    Returns:
        Total used salary (sum of bills + approved advances)
    """
    # Sum of all bills for this employee
    bills_sum = (
        db.query(func.coalesce(func.sum(Bill.amount_billed), 0.0))
        .filter(Bill.billed_employee_id == employee_id)
        .scalar()
    )
    
    # Sum of approved advances for this employee
    advances_sum = (
        db.query(func.coalesce(func.sum(Advance.amount_for_advance), 0.0))
        .filter(
            Advance.employee_id == employee_id,
            Advance.status == AdvanceStatus.APPROVED
        )
        .scalar()
    )
    
    used_salary = float(bills_sum or 0) + float(advances_sum or 0)
    return used_salary


def update_employee_used_salary(db: Session, employee_id: int) -> float:
    """
    Update the stored used_salary field for an employee based on current bills and advances.
    
    Args:
        db: Database session
        employee_id: Employee ID
    
    Returns:
        Updated used_salary value
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise ValueError(f"Employee with ID {employee_id} not found")
    
    used_salary = calculate_used_salary_from_transactions(db, employee_id)
    employee.used_salary = used_salary
    employee.updated_at = datetime.now()
    db.commit()
    db.refresh(employee)
    
    return used_salary


def reset_monthly_salary_for_new_month(db: Session, target_date: date = None) -> dict:
    """
    Reset monthly salary for all employees at the start of a new month.
    Carries forward negative balances (debts) to the new month.
    
    Logic:
    - If remaining_salary is negative (used_salary > salary), carry forward the excess
      as the starting used_salary for the new month
    - Otherwise, reset used_salary to 0
    
    Args:
        db: Database session
        target_date: Date to check (defaults to today). If it's the 1st of a month,
                    will reset monthly salary.
    
    Returns:
        Dictionary with reset statistics
    """
    if target_date is None:
        target_date = date.today()
    
    # Only reset on the 1st of the month
    if target_date.day != 1:
        return {
            'reset_count': 0,
            'carried_forward': 0,
            'reset_to_zero': 0
        }
    
    employees = db.query(Employee).all()
    
    stats = {
        'reset_count': 0,
        'carried_forward': 0,
        'reset_to_zero': 0
    }
    
    for employee in employees:
        if employee.used_salary is None:
            employee.used_salary = 0.0
        
        base_salary = float(employee.salary or 0)
        current_used_salary = float(employee.used_salary or 0)
        
        # Calculate remaining salary (can be negative)
        remaining_salary = base_salary - current_used_salary
        
        # If remaining is negative (they owe money), carry forward the excess
        if remaining_salary < 0:
            # Carry forward the debt (excess used salary beyond base salary)
            excess = current_used_salary - base_salary
            employee.used_salary = excess  # Start new month with the debt
            stats['carried_forward'] += 1
            stats['reset_count'] += 1
        elif current_used_salary > 0:
            # Reset to zero if they had positive used salary
            employee.used_salary = 0.0
            stats['reset_to_zero'] += 1
            stats['reset_count'] += 1
    
    if stats['reset_count'] > 0:
        db.commit()
    
    return stats


def get_remaining_salary(employee: Employee) -> float:
    """
    Calculate remaining salary for an employee using stored used_salary.
    
    Args:
        employee: Employee object
    
    Returns:
        Remaining salary (can be negative if used_salary exceeds salary)
    """
    base_salary = float(employee.salary or 0)
    used_salary = float(employee.used_salary or 0)
    remaining = base_salary - used_salary
    return remaining
