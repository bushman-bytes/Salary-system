"""
Ensure an admin employee exists in the database.
Creates a default admin if no admin employee exists.
Safe to run multiple times (idempotent).
"""
import sys
from pathlib import Path
from datetime import datetime, date

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.models.schema import get_engine, get_session, Employee, Role, UserAuth
from app.config.config import DATABASE_URL


def ensure_admin_exists(
    first_name: str = "Admin",
    last_name: str = "User",
    phone_no: str = "+1234567800",
    salary: float = 10000.0,
    pin: int = 4326,
    employment_start_date: date = None
):
    """
    Ensure an admin employee exists in the database.
    
    Args:
        first_name: Admin's first name (default: "Admin")
        last_name: Admin's last name (default: "User")
        phone_no: Admin's phone number (must be unique, default: "+1234567800")
        salary: Admin's salary (default: 10000.0)
        pin: 4-digit PIN for login (default: 4326)
        employment_start_date: Start date (default: today)
    
    Returns:
        tuple: (admin_employee, created_new) - Employee object and boolean indicating if new admin was created
    """
    if employment_start_date is None:
        employment_start_date = date.today()
    
    engine = get_engine(DATABASE_URL)
    session = get_session(engine)
    
    try:
        # Check if any admin employee already exists
        existing_admin = session.query(Employee).filter(Employee.role == Role.ADMIN).first()
        
        if existing_admin:
            print(f"✓ Admin employee already exists:")
            print(f"  ID: {existing_admin.id}")
            print(f"  Name: {existing_admin.first_name} {existing_admin.last_name}")
            print(f"  Phone: {existing_admin.phone_no}")
            print(f"  Role: {existing_admin.role.value}")
            
            # Check if UserAuth entry exists for this admin
            user_auth = session.query(UserAuth).filter(
                UserAuth.first_name == existing_admin.first_name
            ).first()
            
            if not user_auth:
                print(f"\n⚠ UserAuth entry not found for admin. Creating one...")
                user_auth = UserAuth(
                    first_name=existing_admin.first_name,
                    pin=pin
                )
                session.add(user_auth)
                session.commit()
                print(f"✓ Created UserAuth entry with PIN: {pin}")
            
            return existing_admin, False
        
        # No admin exists, create one
        print(f"Creating admin employee...")
        print(f"  Name: {first_name} {last_name}")
        print(f"  Phone: {phone_no}")
        print(f"  Salary: {salary}")
        print(f"  PIN: {pin}")
        
        # Check if phone number already exists
        existing_phone = session.query(Employee).filter(Employee.phone_no == phone_no).first()
        if existing_phone:
            raise ValueError(
                f"Phone number {phone_no} already exists for employee "
                f"'{existing_phone.first_name} {existing_phone.last_name}'. "
                f"Please use a different phone number."
            )
        
        # Create admin employee
        admin_employee = Employee(
            first_name=first_name,
            last_name=last_name,
            role=Role.ADMIN,
            salary=salary,
            phone_no=phone_no,
            employment_start_date=employment_start_date,
            days_worked_this_month=0,
            total_days_worked=0,
            used_salary=0.0
        )
        
        session.add(admin_employee)
        session.flush()  # Flush to get the ID
        
        # Create UserAuth entry for login
        user_auth = UserAuth(
            first_name=first_name,
            pin=pin
        )
        
        session.add(user_auth)
        session.commit()
        session.refresh(admin_employee)
        session.refresh(user_auth)
        
        print(f"\n✓ Admin employee created successfully!")
        print(f"  Employee ID: {admin_employee.id}")
        print(f"  Name: {admin_employee.first_name} {admin_employee.last_name}")
        print(f"  Phone: {admin_employee.phone_no}")
        print(f"  Role: {admin_employee.role.value}")
        print(f"  UserAuth ID: {user_auth.id}")
        print(f"  Login with: first_name='{first_name}', PIN={pin}")
        
        return admin_employee, True
        
    except Exception as e:
        session.rollback()
        print(f"\n✗ Error ensuring admin exists: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Ensure Admin Employee Exists")
    print("=" * 60)
    print()
    
    try:
        admin, created = ensure_admin_exists()
        
        if created:
            print("\n" + "=" * 60)
            print("SUCCESS: New admin employee created!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("INFO: Admin employee already exists.")
            print("=" * 60)
            
    except Exception as e:
        print("\n" + "=" * 60)
        print("FAILED: Could not ensure admin exists.")
        print("=" * 60)
        sys.exit(1)
