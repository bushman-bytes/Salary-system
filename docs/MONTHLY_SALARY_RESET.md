# Monthly Salary Reset System

## Overview

The monthly salary reset system automatically resets the `used_salary` field at the beginning of each month. If an employee has a negative remaining salary (used more than their monthly salary), the debt is carried forward to the new month as the starting `used_salary`.

## How It Works

### Fields

- **`salary`**: Monthly base salary (fixed)
- **`used_salary`**: Amount used this month (bills + approved advances)
- **`remaining_salary`**: Calculated as `salary - used_salary` (can be negative)

### Monthly Reset Logic

At the beginning of each month (1st day):

1. **If remaining salary is negative** (used_salary > salary):
   - Employee owes money (debt)
   - The excess amount (used_salary - salary) is **carried forward**
   - New month's `used_salary` starts with the carried-forward debt

2. **If remaining salary is zero or positive**:
   - `used_salary` is reset to **0**
   - Employee starts fresh for the new month

### Example Scenarios

#### Scenario 1: Employee with Debt (Negative Balance)
- Base salary: KSH 5,000
- Used salary (end of month): KSH 6,000
- Remaining: KSH -1,000 (owes 1,000)

**After reset on 1st:**
- Used salary: KSH 1,000 (debt carried forward)
- New month starts with 1,000 already used

#### Scenario 2: Employee with Positive Balance
- Base salary: KSH 5,000
- Used salary (end of month): KSH 3,000
- Remaining: KSH 2,000

**After reset on 1st:**
- Used salary: KSH 0 (reset)
- New month starts fresh

#### Scenario 3: Employee Used All Salary
- Base salary: KSH 5,000
- Used salary (end of month): KSH 5,000
- Remaining: KSH 0

**After reset on 1st:**
- Used salary: KSH 0 (reset)
- New month starts fresh

## Usage

### Automatic Reset

The reset happens automatically when the daily update script runs on the 1st of each month:

```bash
python scripts/daily_attendance_update.py
```

This script is typically scheduled to run daily (see `DAILY_ATTENDANCE_UPDATE.md`).

### Manual Reset

You can also manually trigger a salary reset:

```python
from app.models.schema import get_engine, get_session
from app.config.config import DATABASE_URL
from app.services.salary_service import reset_monthly_salary_for_new_month
from datetime import date

engine = get_engine(DATABASE_URL)
session = get_session(engine)

# Reset monthly salary (only works on 1st of month)
stats = reset_monthly_salary_for_new_month(session)
print(f"Reset count: {stats['reset_count']}")
print(f"Carried forward debts: {stats['carried_forward']}")
print(f"Reset to zero: {stats['reset_to_zero']}")

session.close()
```

## Database Migration

Before using this feature, you need to add the `used_salary` column to your database:

```bash
python scripts/migrate_add_used_salary_column.py
```

This migration will:
1. Add the `used_salary` column to the `employee` table
2. Populate it with current values calculated from bills and approved advances

## Service Functions

The salary service (`app/services/salary_service.py`) provides several functions:

### `reset_monthly_salary_for_new_month(db, target_date=None)`

Resets monthly salary for all employees at the start of a new month.

**Returns:** Dictionary with statistics:
```python
{
    'reset_count': 5,      # Total employees reset
    'carried_forward': 2,  # Employees with debt carried forward
    'reset_to_zero': 3     # Employees reset to zero
}
```

### `update_employee_used_salary(db, employee_id)`

Updates the stored `used_salary` field for an employee based on current bills and advances.

**Returns:** Updated used_salary value

### `calculate_used_salary_from_transactions(db, employee_id)`

Calculates used salary from bills and approved advances (doesn't update the field).

**Returns:** Calculated used_salary value

### `get_remaining_salary(employee)`

Calculates remaining salary using stored `used_salary`.

**Returns:** Remaining salary (can be negative)

## Integration with Daily Update Script

The daily update script (`scripts/daily_attendance_update.py`) automatically handles:
1. Monthly attendance reset (on 1st of month)
2. Monthly salary reset (on 1st of month)
3. Daily attendance updates

When run on the 1st, you'll see output like:

```
First day of month detected - resetting monthly data...
✓ Reset monthly attendance for 10 employees
✓ Reset monthly salary:
  - Carried forward debts: 2
  - Reset to zero: 8
```

## Keeping Used Salary in Sync

The `used_salary` field should be kept in sync with actual bills and advances. You can update it manually:

```python
from app.services.salary_service import update_employee_used_salary

# Update after adding a bill or approving an advance
update_employee_used_salary(session, employee_id)
```

Alternatively, you can integrate this into your bill/advance services to automatically update `used_salary` when transactions occur.

## Notes

- The system allows `used_salary` to exceed `salary` (negative remaining salary)
- Negative balances (debts) are automatically carried forward to the next month
- The reset only occurs on the 1st of each month
- If the daily script doesn't run on the 1st, you can run it manually or reschedule
- The `used_salary` field is a stored value for performance, but can be recalculated from transactions if needed

## Troubleshooting

### Reset Not Happening

1. Ensure the daily script is scheduled to run daily
2. Check that it's running on the 1st of the month
3. Manually run the reset function if needed

### Incorrect Used Salary Values

1. Recalculate using `update_employee_used_salary()`
2. Or run the migration script again to recalculate all values

### Debt Not Carried Forward

1. Check that remaining salary was actually negative before reset
2. Verify the reset function ran on the 1st
3. Check database directly to see `used_salary` values
