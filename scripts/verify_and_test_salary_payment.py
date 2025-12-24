"""
Verify salary payment table exists and test inserting a payment.
This script will help diagnose why payments aren't being saved to the database.
"""
import sys
import os
from pathlib import Path
from datetime import date

# Add parent directory to path to allow imports
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text, inspect
from sqlalchemy.orm import sessionmaker
from app.models.schema import get_engine, Employee, SalaryPayment, Role
from app.config.config import DATABASE_URL
from app.services.salary_payment_service import record_salary_payment


def verify_table():
    """Verify the salary_payment table exists"""
    print("=" * 60)
    print("Step 1: Verifying Table Exists")
    print("=" * 60)
    
    engine = get_engine(DATABASE_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if 'salary_payment' not in tables:
        print("✗ salary_payment table does NOT exist!")
        print("\nPlease run the migration script:")
        print("  python scripts/migrate_add_salary_payment_table.py")
        return False
    
    print("✓ salary_payment table exists")
    
    # Check columns
    columns = inspector.get_columns('salary_payment')
    print(f"\nTable has {len(columns)} columns:")
    for col in columns:
        nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
        print(f"  - {col['name']}: {col['type']} ({nullable})")
    
    return True


def test_insert():
    """Test inserting a payment record"""
    print("\n" + "=" * 60)
    print("Step 2: Testing Payment Insert")
    print("=" * 60)
    
    engine = get_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Get first employee and admin
        employees = session.query(Employee).limit(5).all()
        if not employees:
            print("✗ No employees found in database!")
            return False
        
        print(f"\nFound {len(employees)} employees:")
        for emp in employees:
            role_val = emp.role.value if hasattr(emp.role, 'value') else str(emp.role)
            print(f"  - {emp.id}: {emp.first_name} {emp.last_name} ({role_val})")
        
        # Find an admin
        admin = session.query(Employee).filter(Employee.role == Role.ADMIN).first()
        if not admin:
            print("\n✗ No admin user found!")
            print("  You need at least one admin user to record payments.")
            return False
        
        print(f"\n✓ Admin found: {admin.first_name} {admin.last_name} (ID: {admin.id})")
        
        # Get first non-admin employee for testing
        test_employee = session.query(Employee).filter(Employee.role != Role.ADMIN).first()
        if not test_employee:
            print("\n✗ No non-admin employees found for testing!")
            return False
        
        print(f"\n✓ Test employee: {test_employee.first_name} {test_employee.last_name} (ID: {test_employee.id})")
        
        # Count existing payments
        existing_count = session.query(SalaryPayment).count()
        print(f"\nCurrent payment records in database: {existing_count}")
        
        # Try to record a test payment
        print("\nAttempting to record a test payment...")
        print(f"  Employee: {test_employee.first_name} {test_employee.last_name}")
        print(f"  Admin: {admin.first_name} {admin.last_name}")
        print(f"  Amount: KSH 100.00 (test)")
        
        try:
            payment = record_salary_payment(
                db=session,
                employee_id=test_employee.id,
                admin_id=admin.id,
                amount_paid=100.00,
                payment_date=date.today(),
                notes="Test payment - can be deleted"
            )
            
            print(f"\n✓ Payment recorded successfully!")
            print(f"  Payment ID: {payment.id}")
            print(f"  Amount: KSH {payment.amount_paid}")
            print(f"  Date: {payment.payment_date}")
            
            # Verify it's in the database
            verify_payment = session.query(SalaryPayment).filter(SalaryPayment.id == payment.id).first()
            if verify_payment:
                print(f"\n✓ Payment verified in database!")
                print(f"  Verified ID: {verify_payment.id}")
            else:
                print(f"\n✗ Payment not found in database after commit!")
                return False
            
            # Count payments again
            new_count = session.query(SalaryPayment).count()
            print(f"\nPayment records after insert: {new_count}")
            if new_count > existing_count:
                print("✓ Payment count increased - data is being saved!")
            else:
                print("✗ Payment count did not increase!")
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error recording payment: {str(e)}")
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}")
            session.rollback()
            return False
            
    finally:
        session.close()


def check_employee_salary_status():
    """Check employee salary status"""
    print("\n" + "=" * 60)
    print("Step 3: Checking Employee Salary Status")
    print("=" * 60)
    
    engine = get_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        employees = session.query(Employee).limit(5).all()
        print(f"\nSalary status for {len(employees)} employees:")
        for emp in employees:
            used = float(emp.used_salary or 0)
            salary = float(emp.salary or 0)
            remaining = salary - used
            print(f"\n  {emp.first_name} {emp.last_name}:")
            print(f"    Base Salary: KSH {salary:,.2f}")
            print(f"    Used Salary: KSH {used:,.2f}")
            print(f"    Remaining: KSH {remaining:,.2f}")
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Salary Payment Table Verification & Test")
    print("=" * 60)
    print()
    
    try:
        # Step 1: Verify table exists
        if not verify_table():
            print("\n⚠ Please create the table first using the migration script.")
            sys.exit(1)
        
        # Step 2: Test inserting a payment
        if test_insert():
            print("\n" + "=" * 60)
            print("✓ All tests passed!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("✗ Some tests failed - check errors above")
            print("=" * 60)
            sys.exit(1)
        
        # Step 3: Check salary status
        check_employee_salary_status()
        
    except Exception as e:
        import traceback
        print(f"\n✗ Unexpected error: {str(e)}")
        print(f"Traceback:\n{traceback.format_exc()}")
        sys.exit(1)
