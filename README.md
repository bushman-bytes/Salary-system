# Salary Management System

A comprehensive salary management system built with Python and Cloud Database (PostgreSQL-compatible).

## Features

### Role-Based Access Control feature

- **Staff**: Can request advances 
- **Manager**: Can request advances, and can add/update bills for staff members and other managers
- **Admin**: Can approve advances, add bills for staff and managers, view all bills and advances, and send notifications

### Functionality

1. **Advance Requests**: Staff members and managers can request salary advances with approval workflow
2. **Bill Management**: Managers and admins can record bills for staff members and managers with metadata (date, amount, reason, recorded by information)
3. **Notifications**: Admins can receive email/WhatsApp notifications; new advance and off-day requests can email a configured admin address. See [docs/ADMIN_EMAIL_AND_ATTENDANCE.md](docs/ADMIN_EMAIL_AND_ATTENDANCE.md).

## Database Schema

### Employee Table
- `id`: Primary key
- `first_name`: Employee's first name
- `last_name`: Employee's last name
- `role`: Role (staff, manager, admin)
- `salary`: Monthly salary
- `phone_no`: Phone number (unique)
- `created_at`: Record creation timestamp
- `updated_at`: Record update timestamp

### Bill_Advances Table
- `id`: Primary key
- `pin`: Unique identifier
- `first_name`: Quick reference name
- `record_type`: 'advance' or 'bill'
- `employee_id`: Employee who requested advance (staff or manager)
- `billed_employee_id`: Employee the bill is for (staff or manager)
- `amount`: Amount
- `date`: Date of bill/advance
- `reason`: Optional reason
- `status`: Status for advances (pending, approved, denied)
- `recorded_by_id`: Who recorded this information
- `manager_name`: Manager/Admin name linked to bill (who recorded it)
- `approved_by_id`: Admin who approved/denied
- `approved_at`: Approval timestamp
- `approval_notes`: Notes from approver

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   - Copy `.env.example` to `.env`
   - Fill in your Neon database connection string
   - Configure email and WhatsApp credentials (optional)

3. **Initialize database**:
   ```bash
   python scripts/init_db.py
   ```

## Project Structure

```
Salary_Management_system/
├── app/                          # Main application package
│   ├── models/                   # Database models
│   │   ├── __init__.py
│   │   └── schema.py            # Database schema definitions
│   ├── services/                 # Business logic services
│   │   ├── __init__.py
│   │   ├── advance_service.py   # Advance request handling
│   │   ├── auth_service.py       # Role-based permissions
│   │   ├── bill_service.py       # Bill management
│   │   └── notification_service.py  # Email/WhatsApp notifications
│   └── config/                   # Configuration
│       ├── __init__.py
│       └── config.py             # Environment variables & settings
├── templates/                     # HTML templates
│   ├── login.html               # Login page
│   └── admin_dashboard.html     # Admin dashboard page
├── static/                       # Static assets
│   ├── images/
│   │   └── logo.jpg             # Application logo
│   └── videos/
│       └── login_abstract.mp4   # Background video
├── scripts/                      # Utility scripts
│   ├── init_db.py               # Database initialization
│   ├── example_usage.py         # Example usage demonstrations
│   └── utils.py                 # Utility functions
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
└── .gitignore                   # Git ignore rules
```

## Usage

### Importing Modules

```python
# Import models
from app.models import Employee, BillAdvance, Role, AdvanceStatus

# Import services
from app.services import (
    request_advance,
    approve_advance,
    add_bill,
    can_request_advance
)

# Import configuration
from app.config import DATABASE_URL, EMAIL_HOST
```

### Running Scripts

```bash
# Initialize database
python scripts/init_db.py

# Create sample data
python scripts/utils.py

# Run example workflow
python scripts/example_usage.py
```

## Web Interface

A modern, responsive web interface is included:

- **`templates/login.html`**: Beautiful login page with:
  - Moving abstract video background
  - Modern CSS features (gradients, animations, backdrop-filter)
  - Fully responsive design optimized for mobile devices
  - Role-based login form
  - Password visibility toggle
  - Remember me functionality
  - Mobile-first design (prevents zoom on iOS)

- **`templates/admin_dashboard.html`**: Admin dashboard page (ready for backend integration)

### Opening the Web Interface

Simply open `templates/login.html` in your web browser:
```bash
# Using Python's built-in server
python -m http.server 8000
# Then navigate to http://localhost:8000/templates/login.html
```

Or open the file directly in your browser (double-click `templates/login.html`).

