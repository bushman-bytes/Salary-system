# Salary Payment Troubleshooting Guide

## Issue: Payments Display on Dashboard but Not Saved to Database

If you're seeing payments appear on the dashboard but they're not actually being saved to the database, follow these steps:

## Step 1: Verify Table Exists

The `salary_payment` table must exist in your Neon database. Run this script to check and create it if needed:

```bash
python scripts/migrate_add_salary_payment_table.py
```

Or use the simpler verification script:

```bash
python scripts/ensure_salary_payment_table.py
```

Or create all tables (including salary_payment):

```bash
python scripts/init_db.py
```

## Step 2: Check for Errors

When you click "Pay Salary", check:

1. **Browser Console** (F12 → Console tab):
   - Look for any error messages
   - Check if the API call is successful (status 201)

2. **Server Logs**:
   - Check the terminal/console where your FastAPI server is running
   - Look for error messages about database operations

## Step 3: Verify Database Connection

Make sure your `DATABASE_URL` in `.env` is correct and points to your Neon database.

## Step 4: Check Table Structure

Verify the table structure matches what's expected. You can check in Neon dashboard:

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'salary_payment';
```

Expected columns:
- `id` (SERIAL/INTEGER)
- `employee_id` (INTEGER)
- `amount_paid` (FLOAT/REAL)
- `payment_date` (DATE)
- `notes` (TEXT)
- `paid_by_id` (INTEGER)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

## Step 5: Test Payment Recording

You can test if payments are being saved by running:

```bash
python scripts/verify_and_test_salary_payment.py
```

This will:
- Check if the table exists
- Try to insert a test payment
- Verify it's saved correctly

## Common Issues

### Issue 1: Table Doesn't Exist

**Symptoms:** API returns 500 error or payment appears to work but nothing in DB

**Solution:** Run the migration script:
```bash
python scripts/migrate_add_salary_payment_table.py
```

### Issue 2: Foreign Key Constraint Error

**Symptoms:** Error about employee_id or paid_by_id not existing

**Solution:** Make sure:
- Employee records exist
- Admin user exists
- IDs are correct

### Issue 3: Permission Error

**Symptoms:** Error saying "Only admins can record salary payments"

**Solution:** Make sure the `admin_id` in the API call belongs to an employee with role = 'admin'

### Issue 4: Session/Transaction Issue

**Symptoms:** Payment appears to save but doesn't persist

**Solution:** The code now includes explicit commit() calls. If issues persist:
- Check database connection is stable
- Verify no connection timeouts
- Check Neon database logs

## Verification Queries

To check if payments are being saved, run these in Neon SQL Editor:

```sql
-- Check if table exists
SELECT COUNT(*) FROM salary_payment;

-- See all payments
SELECT 
    sp.id,
    e.first_name || ' ' || e.last_name as employee_name,
    sp.amount_paid,
    sp.payment_date,
    admin.first_name || ' ' || admin.last_name as paid_by
FROM salary_payment sp
JOIN employee e ON sp.employee_id = e.id
JOIN employee admin ON sp.paid_by_id = admin.id
ORDER BY sp.created_at DESC;
```

## Next Steps

If payments still aren't saving after following these steps:

1. Check server error logs for detailed error messages
2. Verify database connection string is correct
3. Test with the verification script
4. Check Neon database logs for connection issues

## Contact Support

If the issue persists, provide:
- Error messages from browser console
- Error messages from server logs
- Output from verification script
- Database connection status
