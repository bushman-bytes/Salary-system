"""
Test script to verify salary payment table and functionality.
Use this to check if the table exists and if data can be inserted.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to allow imports
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text, inspect
from app.models.schema import get_engine, Employee, SalaryPayment, Role
from app.config.config import DATABASE_URL


def test_table_exists():
    """Check if salary_payment table exists"""
    print("=" * 60)
    print("Testing Salary Payment Table")
    print("=" * 60)
    
    engine = get_engine(DATABASE_URL)
    
    # Check if table exists
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\n1. Checking if 'salary_payment' table exists...")
    if 'salary_payment' in tables:
        print("   ✓ salary_payment table exists")
        
        # Get column information
        columns = inspector.get_columns('salary_payment')
        print(f"\n2. Table columns:")
        for col in columns:
            print(f"   - {col['name']}: {col['type']}")
    else:
        print("   ✗ salary_payment table NOT found!")
        print("   Available tables:", tables)
        print("\n   Run the migration script:")
        print("   python scripts/migrate_add_salary_payment_table.py")
        return False
    
    # Check for foreign key constraints
    print(f"\n3. Checking foreign key constraints...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = 'salary_payment'
        """))
        
        fks = result.fetchall()
        if fks:
            print("   ✓ Foreign keys found:")
            for fk in fks:
                print(f"   - {fk[2]} -> {fk[3]}.{fk[4]}")
        else:
            print("   ⚠ No foreign keys found (might be missing)")
    
    # Check employee table exists (required for foreign key)
    print(f"\n4. Checking employee table...")
    if 'employee' in tables:
        print("   ✓ employee table exists")
        
        # Count employees
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM employee"))
            count = result.scalar()
            print(f"   - Total employees: {count}")
            
            # Check for admin employees
            result = conn.execute(text("SELECT COUNT(*) FROM employee WHERE role = 'admin'"))
            admin_count = result.scalar()
            print(f"   - Admin employees: {admin_count}")
    else:
        print("   ✗ employee table NOT found!")
        return False
    
    # Try to query existing salary payments
    print(f"\n5. Checking existing salary payment records...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM salary_payment"))
        count = result.scalar()
        print(f"   - Existing salary payments: {count}")
        
        if count > 0:
            result = conn.execute(text("""
                SELECT id, employee_id, amount_paid, payment_date, paid_by_id
                FROM salary_payment
                ORDER BY created_at DESC
                LIMIT 5
            """))
            payments = result.fetchall()
            print(f"\n   Recent payments:")
            for payment in payments:
                print(f"   - ID: {payment[0]}, Employee: {payment[1]}, Amount: {payment[2]}, Date: {payment[3]}")
    
    print("\n" + "=" * 60)
    print("Table check complete!")
    print("=" * 60)
    
    return True


def test_insert_payment():
    """Test inserting a payment (dry run)"""
    print("\n" + "=" * 60)
    print("Testing Payment Insert (Dry Run)")
    print("=" * 60)
    
    engine = get_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Get first employee and admin
        result = conn.execute(text("""
            SELECT id, first_name, last_name, role
            FROM employee
            LIMIT 5
        """))
        employees = result.fetchall()
        
        if not employees:
            print("   ✗ No employees found in database!")
            return
        
        print(f"\n   Found {len(employees)} employees:")
        for emp in employees:
            role_str = emp[3] if isinstance(emp[3], str) else (emp[3].value if hasattr(emp[3], 'value') else str(emp[3]))
            print(f"   - ID: {emp[0]}, Name: {emp[1]} {emp[2]}, Role: {role_str}")
        
        # Find an admin
        result = conn.execute(text("""
            SELECT id, first_name, last_name
            FROM employee
            WHERE role = 'admin'
            LIMIT 1
        """))
        admin = result.fetchone()
        
        if not admin:
            print("\n   ⚠ No admin found! Cannot test payment recording.")
            print("   Payment recording requires an admin user.")
            return
        
        print(f"\n   Admin found: {admin[1]} {admin[2]} (ID: {admin[0]})")
        print("\n   ✓ Table structure looks good for inserting payments")
    
    print("\n" + "=" * 60)
    print("Insert test complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        if test_table_exists():
            test_insert_payment()
        else:
            print("\n⚠ Please run the migration script first:")
            print("   python scripts/migrate_add_salary_payment_table.py")
    except Exception as e:
        import traceback
        print(f"\n✗ Error during test: {str(e)}")
        print(f"Traceback:\n{traceback.format_exc()}")
