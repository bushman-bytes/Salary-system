"""
Migration script to create salary_payment table.
Run this script to add the salary payment tracking table.
"""
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from app.models.schema import get_engine
from app.config.config import DATABASE_URL


def migrate():
    """Create salary_payment table if it doesn't exist."""
    print("Connecting to database...")
    engine = get_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if table already exists
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'salary_payment'
        """))
        table_exists = result.fetchone() is not None
        
        if table_exists:
            print("✓ salary_payment table already exists")
        else:
            print("Creating salary_payment table...")
            conn.execute(text("""
                CREATE TABLE salary_payment (
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
            print("✓ Created salary_payment table")
            
            # Create index on employee_id for faster queries
            print("Creating indexes...")
            conn.execute(text("""
                CREATE INDEX idx_salary_payment_employee_id ON salary_payment(employee_id)
            """))
            conn.execute(text("""
                CREATE INDEX idx_salary_payment_payment_date ON salary_payment(payment_date)
            """))
            conn.commit()
            print("✓ Created indexes")
    
    print("\nMigration complete!")


if __name__ == "__main__":
    migrate()
