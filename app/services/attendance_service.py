"""
Service for handling daily employee attendance updates.
Updates days_worked_this_month and total_days_worked fields daily.
"""
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from app.models.schema import Employee, OffDay, OffDayStatus


def is_today_off_day(db: Session, employee_id: int, check_date: date = None) -> bool:
    """
    Check if a specific date is an approved off day for an employee.
    
    Args:
        db: Database session
        employee_id: Employee ID
        check_date: Date to check (defaults to today)
    
    Returns:
        True if the date is an approved off day, False otherwise
    """
    if check_date is None:
        check_date = date.today()
    
    # Get all approved off days that might cover this date
    off_days = db.query(OffDay).filter(
        OffDay.employee_id == employee_id,
        OffDay.status == OffDayStatus.APPROVED
    ).all()
    
    for off_day in off_days:
        # Calculate the range of dates for this off day request
        off_day_start = off_day.date
        off_day_end = off_day_start + timedelta(days=off_day.day_count - 1)
        
        # Check if check_date falls within this range
        if off_day_start <= check_date <= off_day_end:
            return True
    
    return False


def update_employee_attendance_for_date(
    db: Session,
    employee: Employee,
    update_date: date = None
) -> bool:
    """
    Update employee attendance for a specific date.
    Increments days_worked_this_month and total_days_worked if the date
    is a working day (not an approved off day).
    
    Args:
        db: Database session
        employee: Employee object
        update_date: Date to update for (defaults to today)
    
    Returns:
        True if attendance was updated, False if it was an off day or before employment start
    """
    if update_date is None:
        update_date = date.today()
    
    # Don't count days before employment start
    if update_date < employee.employment_start_date:
        return False
    
    # Check if this is an off day
    if is_today_off_day(db, employee.id, update_date):
        return False
    
    # Initialize counters if None
    if employee.days_worked_this_month is None:
        employee.days_worked_this_month = 0
    if employee.total_days_worked is None:
        employee.total_days_worked = 0
    
    # Check if we need to reset days_worked_this_month (new month)
    current_month = update_date.month
    current_year = update_date.year
    
    # Get the last update date to determine if month changed
    last_update_date = None
    if employee.updated_at:
        last_update_date = employee.updated_at.date()
    
    # Reset monthly counter if this is the first update of a new month
    if last_update_date:
        if last_update_date.month != current_month or last_update_date.year != current_year:
            # New month detected - reset monthly counter
            employee.days_worked_this_month = 0
    elif update_date.day == 1:
        # First time updating and it's the 1st - ensure monthly counter is 0
        employee.days_worked_this_month = 0
    
    # Check if we already counted today
    if last_update_date == update_date:
        # Already updated today, don't double count
        return False
    
    # Increment both counters
    employee.days_worked_this_month += 1
    employee.total_days_worked += 1
    
    # Update the updated_at timestamp
    employee.updated_at = datetime.now()
    
    db.commit()
    db.refresh(employee)
    
    return True


def update_all_employees_attendance(
    db: Session,
    update_date: date = None
) -> dict:
    """
    Update attendance for all active employees for a specific date.
    
    Args:
        db: Database session
        update_date: Date to update for (defaults to today)
    
    Returns:
        Dictionary with update statistics
    """
    if update_date is None:
        update_date = date.today()
    
    # Get all employees who have started employment
    employees = db.query(Employee).filter(
        Employee.employment_start_date <= update_date
    ).all()
    
    stats = {
        'total_employees': len(employees),
        'updated': 0,
        'off_days': 0,
        'not_started': 0,
        'already_counted': 0
    }
    
    for employee in employees:
        # Check if already updated today
        if employee.updated_at and employee.updated_at.date() == update_date:
            stats['already_counted'] += 1
            continue
        
        # Don't count before employment start
        if update_date < employee.employment_start_date:
            stats['not_started'] += 1
            continue
        
        # Check if already updated today (early exit for efficiency)
        if employee.updated_at and employee.updated_at.date() == update_date:
            stats['already_counted'] += 1
            continue
        
        # Check if off day
        if is_today_off_day(db, employee.id, update_date):
            stats['off_days'] += 1
            # Still update the timestamp to track that we processed today
            # (to prevent reprocessing if script runs multiple times)
            employee.updated_at = datetime.now()
            db.commit()
            continue
        
        # Update attendance
        if update_employee_attendance_for_date(db, employee, update_date):
            stats['updated'] += 1
    
    return stats


def reset_monthly_attendance_for_new_month(db: Session, target_date: date = None) -> int:
    """
    Reset days_worked_this_month for all employees at the start of a new month.
    This should be called once per month.
    
    Args:
        db: Database session
        target_date: Date to check (defaults to today). If it's the 1st of a month,
                    will reset monthly counts.
    
    Returns:
        Number of employees whose monthly attendance was reset
    """
    if target_date is None:
        target_date = date.today()
    
    # Only reset on the 1st of the month
    if target_date.day != 1:
        return 0
    
    # Get all employees
    employees = db.query(Employee).all()
    
    reset_count = 0
    for employee in employees:
        # Reset days_worked_this_month at the start of each month
        if employee.days_worked_this_month is not None and employee.days_worked_this_month > 0:
            employee.days_worked_this_month = 0
            reset_count += 1
    
    if reset_count > 0:
        db.commit()
    
    return reset_count
