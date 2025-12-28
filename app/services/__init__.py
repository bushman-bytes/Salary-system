"""
Services Package
"""

from .advance_service import (
    request_advance,
    approve_advance,
    get_pending_advances,
    get_employee_advances
)

from .bill_service import (
    add_bill,
    update_bill,
    get_employee_bills,
    get_staff_bills,
    get_all_bills,
    get_recorded_bills
)

from .auth_service import (
    check_permission,
    can_request_advance,
    can_add_bills,
    can_approve_advances,
    can_view_all
)

from .notification_service import (
    send_email_notification,
    send_whatsapp_notification,
    send_pending_advances_summary,
    send_advance_decision_notification
)

from .attendance_service import (
    is_today_off_day,
    update_employee_attendance_for_date,
    update_all_employees_attendance,
    reset_monthly_attendance_for_new_month
)

from .salary_service import (
    calculate_used_salary_from_transactions,
    update_employee_used_salary,
    reset_monthly_salary_for_new_month,
    get_remaining_salary
)

from .salary_payment_service import (
    record_salary_payment,
    get_employee_salary_payments,
    get_all_salary_payments,
    get_salary_payment_by_id
)

__all__ = [
    # Advance service
    'request_advance',
    'approve_advance',
    'get_pending_advances',
    'get_employee_advances',
    # Bill service
    'add_bill',
    'update_bill',
    'get_employee_bills',
    'get_staff_bills',
    'get_all_bills',
    'get_recorded_bills',
    # Auth service
    'check_permission',
    'can_request_advance',
    'can_add_bills',
    'can_approve_advances',
    'can_view_all',
    # Notification service
    'send_email_notification',
    'send_whatsapp_notification',
    'send_pending_advances_summary',
    'send_advance_decision_notification',
    # Attendance service
    'is_today_off_day',
    'update_employee_attendance_for_date',
    'update_all_employees_attendance',
    'reset_monthly_attendance_for_new_month',
    # Salary service
    'calculate_used_salary_from_transactions',
    'update_employee_used_salary',
    'reset_monthly_salary_for_new_month',
    'get_remaining_salary',
    # Salary payment service
    'record_salary_payment',
    'get_employee_salary_payments',
    'get_all_salary_payments',
    'get_salary_payment_by_id'
]

