"""
Service for handling salary payments.
Records salary payments and updates employee used_salary accordingly.
"""
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.models.schema import Employee, SalaryPayment, Role
from app.services.salary_service import calculate_used_salary_from_transactions, get_remaining_salary


def record_salary_payment(
    db: Session,
    employee_id: int,
    admin_id: int,
    amount_paid: float = None,
    payment_date: date = None,
    notes: str = None
) -> SalaryPayment:
    """
    Record a salary payment for an employee.
    When salary is paid, resets used_salary to 0 (clearing the balance).
    
    Args:
        db: Database session
        employee_id: ID of employee receiving payment
        admin_id: ID of admin recording the payment
        amount_paid: Amount paid (defaults to remaining salary)
        payment_date: Date of payment (defaults to today)
        notes: Optional notes about the payment
    
    Returns:
        SalaryPayment object
    """
    # Verify employee exists
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise ValueError("Employee not found")
    
    # Verify admin exists and has admin role
    admin = db.query(Employee).filter(Employee.id == admin_id).first()
    if not admin:
        raise ValueError("Admin not found")
    
    if admin.role != Role.ADMIN:
        raise PermissionError("Only admins can record salary payments")
    
    # Calculate remaining salary (what they're owed)
    if payment_date is None:
        payment_date = date.today()
    
    # Calculate current used salary and remaining
    current_used_salary = calculate_used_salary_from_transactions(db, employee_id)
    base_salary = float(employee.salary or 0)
    remaining_salary = base_salary - current_used_salary
    
    # If amount_paid not specified, pay the remaining salary (or 0 if negative)
    if amount_paid is None:
        amount_paid = max(0, remaining_salary)
    
    # Create salary payment record
    salary_payment = SalaryPayment(
        employee_id=employee_id,
        paid_by_id=admin_id,
        amount_paid=amount_paid,
        payment_date=payment_date,
        notes=notes
    )
    
    db.add(salary_payment)
    
    # Reset used_salary to 0 (payment clears the balance)
    # This means bills and advances are now "paid off"
    employee.used_salary = 0.0
    employee.updated_at = datetime.now()
    
    try:
        # Flush to ensure all changes are staged and catch errors early
        db.flush()
        
        # Commit the transaction
        db.commit()
        
        # Refresh to get the updated object with database-generated values
        db.refresh(salary_payment)
        db.refresh(employee)
        
        return salary_payment
    except Exception as e:
        # Rollback on any error
        db.rollback()
        error_msg = f"Database error recording salary payment: {str(e)}"
        print(error_msg)
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        # Re-raise with more context
        raise Exception(f"Failed to save salary payment to database: {str(e)}") from e


def get_employee_salary_payments(db: Session, employee_id: int) -> list:
    """
    Get all salary payment records for an employee.
    
    Args:
        db: Database session
        employee_id: Employee ID
    
    Returns:
        List of SalaryPayment objects, ordered by payment date (newest first)
    """
    return (
        db.query(SalaryPayment)
        .filter(SalaryPayment.employee_id == employee_id)
        .order_by(SalaryPayment.payment_date.desc(), SalaryPayment.created_at.desc())
        .all()
    )


def get_all_salary_payments(db: Session) -> list:
    """
    Get all salary payment records (for admin).
    
    Args:
        db: Database session
    
    Returns:
        List of SalaryPayment objects, ordered by payment date (newest first)
    """
    return (
        db.query(SalaryPayment)
        .order_by(SalaryPayment.payment_date.desc(), SalaryPayment.created_at.desc())
        .all()
    )


def get_salary_payment_by_id(db: Session, payment_id: int) -> SalaryPayment:
    """
    Get a salary payment by ID.
    
    Args:
        db: Database session
        payment_id: Payment ID
    
    Returns:
        SalaryPayment object or None if not found
    """
    return db.query(SalaryPayment).filter(SalaryPayment.id == payment_id).first()
