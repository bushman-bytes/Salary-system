"""
Service for handling advance requests
Staff and Managers can request advances, Admin can approve/deny them
"""

from sqlalchemy.orm import Session
from app.models.schema import Employee, Advance, Role, AdvanceStatus
from datetime import datetime


def request_advance(
    session: Session,
    employee_id: int,
    amount: float,
    reason: str = None,
) -> Advance:
    """
    Staff or Manager can request an advance
    
    Args:
        session: Database session
        employee_id: ID of employee requesting advance
        amount: Advance amount
        reason: Optional reason for advance
        pin: Optional unique pin, if not provided will be auto-generated
    
    Returns:
        BillAdvance object
    """
    # Verify employee exists
    employee = session.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise ValueError("Employee not found")
    
    # Staff and Managers can request advances
    if employee.role not in [Role.STAFF, Role.MANAGER]:
        raise PermissionError("Only staff and managers can request advances")
    
    # Create advance request
    advance = Advance(
        employee_id=employee_id,
        amount_for_advance=amount,
        reason=reason,
        status=AdvanceStatus.PENDING,
    )
    
    session.add(advance)
    session.commit()
    session.refresh(advance)
    
    return advance


def approve_advance(
    session: Session,
    advance_id: int,
    admin_id: int,
    approved: bool,
    notes: str = None
) -> Advance:
    """
    Admin can approve or deny an advance request
    
    Args:
        session: Database session
        advance_id: ID of advance to approve/deny
        admin_id: ID of admin approving/denying
        approved: True to approve, False to deny
        notes: Optional approval notes
    
    Returns:
        Updated BillAdvance object
    """
    # Verify admin exists and has admin role
    admin = session.query(Employee).filter(Employee.id == admin_id).first()
    if not admin:
        raise ValueError("Admin not found")
    
    if admin.role != Role.ADMIN:
        raise PermissionError("Only admins can approve advances")
    
    # Get advance request
    advance = session.query(Advance).filter(Advance.id == advance_id).first()
    
    if not advance:
        raise ValueError("Advance request not found")
    
    if advance.status != AdvanceStatus.PENDING:
        raise ValueError(f"Advance is already {advance.status.value}")
    
    # Update status
    advance.status = AdvanceStatus.APPROVED if approved else AdvanceStatus.DENIED
    advance.approved_at = datetime.utcnow()
    advance.approval_notes = notes
    
    session.commit()
    session.refresh(advance)
    
    return advance


def get_pending_advances(session: Session) -> list:
    """Get all pending advance requests (for admin)"""
    return session.query(Advance).filter(
        Advance.status == AdvanceStatus.PENDING
    ).all()


def get_employee_advances(session: Session, employee_id: int) -> list:
    """Get all advance requests for a specific employee"""
    return (
        session.query(Advance)
        .filter(Advance.employee_id == employee_id)
        .order_by(Advance.created_at.desc())
        .all()
    )

