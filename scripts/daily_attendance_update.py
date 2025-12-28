"""
Daily attendance and salary update script.
This script should be run once per day to update employee attendance counters
and handle monthly salary resets.

Usage:
    python scripts/daily_attendance_update.py

Can be scheduled via:
    - Windows Task Scheduler
    - Linux/Unix cron job
    - Cloud scheduler (e.g., AWS EventBridge, Google Cloud Scheduler)
"""
import sys
import os
from datetime import date

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.schema import get_engine, get_session
from app.config.config import DATABASE_URL
from app.services.attendance_service import (
    update_all_employees_attendance,
    reset_monthly_attendance_for_new_month
)
from app.services.salary_service import (
    reset_monthly_salary_for_new_month
)


def main():
    """Main function to update daily attendance for all employees"""
    print(f"Starting daily attendance update for {date.today()}...")
    
    # Initialize database connection
    engine = get_engine(DATABASE_URL)
    session = get_session(engine)
    
    try:
        today = date.today()
        
        # First, check if we need to reset monthly data (if it's the 1st of the month)
        if today.day == 1:
            print("First day of month detected - resetting monthly data...")
            
            # Reset monthly attendance
            attendance_reset_count = reset_monthly_attendance_for_new_month(session)
            if attendance_reset_count > 0:
                print(f"✓ Reset monthly attendance for {attendance_reset_count} employees")
            
            # Reset monthly salary (carries forward negative balances)
            salary_stats = reset_monthly_salary_for_new_month(session)
            if salary_stats['reset_count'] > 0:
                print(f"✓ Reset monthly salary:")
                print(f"  - Carried forward debts: {salary_stats['carried_forward']}")
                print(f"  - Reset to zero: {salary_stats['reset_to_zero']}")
        
        # Update attendance for all employees
        stats = update_all_employees_attendance(session)
        
        print(f"\n=== Attendance Update Summary ===")
        print(f"Total employees processed: {stats['total_employees']}")
        print(f"✓ Updated (worked today): {stats['updated']}")
        print(f"- Off days: {stats['off_days']}")
        print(f"- Already counted today: {stats['already_counted']}")
        print(f"- Not started employment: {stats['not_started']}")
        print(f"\nDaily update completed successfully!")
        
    except Exception as e:
        print(f"ERROR: Failed to update: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
