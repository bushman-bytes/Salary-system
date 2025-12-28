"""
Migration script to add used_salary column to employee table.
Run this script to update existing database schema.
"""
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text, func
from sqlalchemy.orm import sessionmaker
from app.models.schema import get_engine, Employee, Bill, Advance, AdvanceStatus
from app.config.config import DATABASE_URL


def migrate():
    """Add used_salary column and populate it with calculated values from bills and advances."""
    print("Connecting to database...")
    engine = get_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'employee' 
            AND column_name = 'used_salary'
        """))
        existing_columns = [row[0] for row in result]
        
        # Add used_salary if it doesn't exist
        if 'used_salary' not in existing_columns:
            print("Adding used_salary column...")
            conn.execute(text("""
                ALTER TABLE employee 
                ADD COLUMN used_salary FLOAT DEFAULT 0.0
            """))
            conn.commit()
            print("✓ Added used_salary column")
        else:
            print("✓ used_salary column already exists")
    
    # Now populate the column with calculated values from bills and approved advances
    print("\nCalculating and updating used_salary for all employees...")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        employees = db.query(Employee).all()
        for employee in employees:
            # Calculate current used salary from bills and approved advances
            bills_sum = (
                db.query(func.coalesce(func.sum(Bill.amount_billed), 0.0))
                .filter(Bill.billed_employee_id == employee.id)
                .scalar()
            )
            
            advances_sum = (
                db.query(func.coalesce(func.sum(Advance.amount_for_advance), 0.0))
                .filter(
                    Advance.employee_id == employee.id,
                    Advance.status == AdvanceStatus.APPROVED
                )
                .scalar()
            )
            
            used_salary = float(bills_sum or 0) + float(advances_sum or 0)
            employee.used_salary = used_salary
            print(f"  {employee.first_name} {employee.last_name}: KSH {used_salary:,.2f}")
        
        db.commit()
        print(f"\n✓ Updated used_salary for {len(employees)} employees")
    except Exception as e:
        print(f"Error updating used_salary: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    print("\nMigration complete!")


if __name__ == "__main__":
    migrate()
