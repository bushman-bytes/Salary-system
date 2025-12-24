# Daily Attendance Update System

## Overview

The daily attendance update system automatically increments the `days_worked_this_month` and `total_days_worked` fields for all employees on a daily basis. This ensures that employee attendance counters are kept up-to-date automatically.

## How It Works

### Fields Updated

1. **`days_worked_this_month`**: Incremented by 1 each working day, resets to 0 at the start of each month
2. **`total_days_worked`**: Incremented by 1 each working day, cumulative since employment start date

### Update Logic

- ✅ Counts only days **after** the employee's `employment_start_date`
- ✅ Automatically excludes days with **approved off day requests**
- ✅ Prevents double-counting if the script runs multiple times in one day
- ✅ Automatically resets `days_worked_this_month` at the start of each new month

## Usage

### Manual Execution

Run the script manually from the project root:

```bash
python scripts/daily_attendance_update.py
```

### Scheduled Execution

To automate daily updates, schedule the script to run once per day. The recommended time is early morning (e.g., 1:00 AM) to update the previous day's attendance.

#### Windows Task Scheduler

1. Open **Task Scheduler** (search for it in Windows)
2. Click **Create Basic Task**
3. Name it: "Daily Employee Attendance Update"
4. Set trigger to **Daily** at your preferred time
5. Action: **Start a program**
6. Program/script: Full path to Python executable (e.g., `C:\Python\python.exe`)
7. Add arguments: Full path to the script (e.g., `C:\Users\savin\Desktop\Taistat\Salary_Management_system\scripts\daily_attendance_update.py`)
8. Start in: Project root directory (e.g., `C:\Users\savin\Desktop\Taistat\Salary_Management_system`)
9. Click **Finish**

#### Linux/Unix Cron

Add to your crontab (run `crontab -e`):

```bash
# Run daily at 1:00 AM
0 1 * * * cd /path/to/Salary_Management_system && /usr/bin/python3 scripts/daily_attendance_update.py >> /var/log/attendance_update.log 2>&1
```

#### Cloud Services

**AWS EventBridge (Lambda):**
- Create a Lambda function that runs the script
- Schedule it with EventBridge (formerly CloudWatch Events) to run daily

**Google Cloud Scheduler:**
- Create a Cloud Function that runs the script
- Schedule it with Cloud Scheduler

**Azure Functions:**
- Create a Timer Trigger function
- Schedule it with a cron expression

## Service Functions

The attendance service (`app/services/attendance_service.py`) provides several functions:

### `update_all_employees_attendance(db, update_date=None)`

Updates attendance for all employees for a specific date (defaults to today).

**Returns:** Dictionary with statistics:
```python
{
    'total_employees': 10,
    'updated': 8,          # Employees who worked today
    'off_days': 1,         # Employees on approved off day
    'already_counted': 0,  # Already updated today
    'not_started': 1       # Employees not yet started
}
```

### `update_employee_attendance_for_date(db, employee, update_date=None)`

Updates attendance for a single employee for a specific date.

**Returns:** `True` if updated, `False` if off day or before employment start

### `is_today_off_day(db, employee_id, check_date=None)`

Checks if a specific date is an approved off day for an employee.

**Returns:** `True` if it's an approved off day, `False` otherwise

### `reset_monthly_attendance_for_new_month(db, target_date=None)`

Resets `days_worked_this_month` to 0 for all employees if it's the 1st of a month.

**Returns:** Number of employees reset

## Example Usage in Code

```python
from app.models.schema import get_engine, get_session
from app.config.config import DATABASE_URL
from app.services.attendance_service import update_all_employees_attendance
from datetime import date

# Get database session
engine = get_engine(DATABASE_URL)
session = get_session(engine)

# Update attendance for today
stats = update_all_employees_attendance(session)
print(f"Updated {stats['updated']} employees")

# Update attendance for a specific date
stats = update_all_employees_attendance(session, update_date=date(2024, 1, 15))

session.close()
```

## Troubleshooting

### Script Not Running

1. Check that Python path is correct in your scheduled task
2. Verify that the `DATABASE_URL` environment variable is set correctly
3. Check script logs for errors

### Double Counting

The system prevents double counting by checking the `updated_at` timestamp. If an employee's attendance was already updated today, it won't be updated again.

### Missing Days

If the script doesn't run for a few days, only the current day will be counted when it runs again. The system is designed for daily execution.

To backfill missing days, you would need to:
1. Calculate the missing date range
2. Call `update_employee_attendance_for_date()` for each missing date

### Month Reset Not Working

The monthly reset happens automatically when the script runs on the 1st of a month. If it doesn't reset:

1. Check that the script is running on the 1st
2. Verify that `reset_monthly_attendance_for_new_month()` is being called in the script
3. Check database to ensure `days_worked_this_month` field exists

## Notes

- The system counts **all days as working days** except approved off days
- Weekends and holidays are counted as working days unless they are approved off days
- Off days must be **approved** (status = `APPROVED`) to be excluded from counts
- Half days count as full days for attendance purposes (the increment is 1 day)
- The `updated_at` timestamp is used to track when each employee was last processed
