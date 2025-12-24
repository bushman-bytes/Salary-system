"""
One-step script to ensure salary_payment table exists and is ready.
Run this to fix the issue where payments aren't being saved.
"""
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import inspect, text
from app.models.schema import get_engine, Base, SalaryPayment
from app.config.config import DATABASE_URL

print("=" * 60)
print("Salary Payment Table Fix")
print("=" * 60)
print()

try:
    engine = get_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    # Check if table exists
    tables = inspector.get_table_names()
    print(f"Found {len(tables)} tables in database")
    
    if 'salary_payment' in tables:
        print("✓ salary_payment table already exists")
        
        # Check if it has data
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM salary_payment"))
            count = result.scalar()
            print(f"  - Records in table: {count}")
    else:
        print("✗ salary_payment table does NOT exist")
        print("\nCreating table...")
        
        # Create the table
        Base.metadata.create_all(bind=engine, tables=[SalaryPayment.__table__])
        
        # Verify creation
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        if 'salary_payment' in tables:
            print("✓ Table created successfully!")
        else:
            print("✗ Failed to create table")
            print("\nTrying alternative method...")
            
            # Try direct SQL creation
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS salary_payment (
                        id SERIAL PRIMARY KEY,
                        employee_id INTEGER NOT NULL REFERENCES employee(id),
                        amount_paid FLOAT NOT NULL,
                        payment_date DATE NOT NULL DEFAULT CURRENT_DATE,
                        notes TEXT,
                        paid_by_id INTEGER NOT NULL REFERENCES employee(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
            
            # Verify again
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            if 'salary_payment' in tables:
                print("✓ Table created using direct SQL!")
            else:
                print("✗ Still failed. Check database connection.")
                sys.exit(1)
    
    # Check foreign keys
    print("\nVerifying table structure...")
    with engine.connect() as conn:
        columns = inspector.get_columns('salary_payment')
        print(f"  - Columns: {len(columns)}")
        for col in columns:
            print(f"    • {col['name']}")
    
    print("\n" + "=" * 60)
    print("✓ Table is ready!")
    print("=" * 60)
    print("\nYou can now use the salary payment feature in the admin dashboard.")
    
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    import traceback
    print("\nTraceback:")
    print(traceback.format_exc())
    sys.exit(1)
