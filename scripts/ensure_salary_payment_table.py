"""
Quick script to ensure salary_payment table exists in Neon database.
This will create the table if it doesn't exist.
"""
import sys
import os
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text, inspect
from app.models.schema import get_engine, Base, SalaryPayment
from app.config.config import DATABASE_URL

def ensure_table():
    """Ensure salary_payment table exists"""
    print("Checking if salary_payment table exists...")
    
    engine = get_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    # Check if table exists
    tables = inspector.get_table_names()
    if 'salary_payment' in tables:
        print("✓ salary_payment table already exists")
        return True
    
    print("Table not found. Creating salary_payment table...")
    
    # Create the table using SQLAlchemy
    Base.metadata.create_all(bind=engine, tables=[SalaryPayment.__table__])
    
    # Verify it was created
    tables = inspector.get_table_names()
    if 'salary_payment' in tables:
        print("✓ salary_payment table created successfully!")
        return True
    else:
        print("✗ Failed to create table")
        return False

if __name__ == "__main__":
    try:
        ensure_table()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
