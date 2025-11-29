from datetime import date, datetime
from typing import List, Optional, Literal
from pathlib import Path
import os

from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session, sessionmaker, aliased

from app.config.config import DATABASE_URL
from app.models.schema import (
    get_engine,
    Employee,
    Bill,
    Advance,
    AdvanceStatus,
    Role,
    OffDay,
    OffDayStatus,
    UserAuth,
)
from app.utils.attendance import update_employee_attendance


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

# Initialize database engine with error handling for Vercel
try:
    if not DATABASE_URL or DATABASE_URL == "postgresql://username:password@hostname/database?sslmode=require":
        raise ValueError("DATABASE_URL environment variable is not set or is using default value")
    engine = get_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"Warning: Database connection failed during initialization: {e}")
    print("Database connections will be attempted on first use.")
    engine = None
    SessionLocal = None


def get_db() -> Session:
    global engine, SessionLocal
    
    if SessionLocal is None:
        # Lazy initialization if engine wasn't created at startup
        if DATABASE_URL and DATABASE_URL != "postgresql://username:password@hostname/database?sslmode=require":
            engine = get_engine(DATABASE_URL)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        else:
            raise HTTPException(
                status_code=500,
                detail="Database connection not configured. Please set DATABASE_URL environment variable."
            )
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def calculate_remaining_salary(employee_id: int, db: Session) -> float:
    """
    Calculate remaining salary for an employee.
    Returns: remaining_salary = max(salary - used_salary, 0)
    where used_salary = sum(bills) + sum(approved advances)
    """
    employee = db.query(Employee).get(employee_id)
    if not employee:
        return 0.0
    
    # Sum of all bills for this employee
    bills_sum = (
        db.query(func.coalesce(func.sum(Bill.amount_billed), 0.0))
        .filter(Bill.billed_employee_id == employee_id)
        .scalar()
    )
    
    # Sum of approved advances for this employee
    advances_sum = (
        db.query(func.coalesce(func.sum(Advance.amount_for_advance), 0.0))
        .filter(
            Advance.employee_id == employee_id,
            Advance.status == AdvanceStatus.APPROVED,
        )
        .scalar()
    )
    
    used = float(bills_sum or 0) + float(advances_sum or 0)
    salary = float(employee.salary or 0)
    remaining = max(salary - used, 0.0)
    
    return remaining


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class EmployeeBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    role: Literal["staff", "manager"]
    salary: float = Field(..., gt=0)
    phone_no: str = Field(..., max_length=20)
    employment_start_date: Optional[date] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeOut(EmployeeBase):
    id: int
    days_worked_this_month: Optional[int] = None
    total_days_worked: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('role', mode='before')
    @classmethod
    def convert_role_enum(cls, v):
        """Convert Role enum to string value before validation."""
        if isinstance(v, Role):
            return v.value
        return v


class AdvanceCreate(BaseModel):
    employee_id: int
    amount: float = Field(..., gt=0)
    reason: Optional[str] = None


class AdvanceOut(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    amount_for_advance: float
    reason: Optional[str] = None
    status: str
    created_at: datetime
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OffDayCreate(BaseModel):
    employee_id: int
    date: date
    day_count: int = Field(..., gt=0)
    off_type: Literal["full", "half"]
    reason: Optional[str] = None


class OffDayOut(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    days_worked_this_month: Optional[int] = None
    total_days_worked: Optional[int] = None
    date: date
    day_count: int
    off_type: str
    reason: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SalarySummaryItem(BaseModel):
    employee_id: int
    first_name: str
    last_name: str
    role: str
    salary: float
    used_salary: float
    remaining_salary: float


class BillOut(BaseModel):
    id: int
    date: datetime
    employee_id: int
    employee_name: str
    role: str
    amount: float
    reason: Optional[str] = None
    record_type: str
    recorded_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserAuthCreate(BaseModel):
    employee_id: int
    pin: int = Field(..., ge=0, le=9999)


class UserAuthOut(BaseModel):
    id: int
    pin: int
    first_name: str

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    first_name: Optional[str] = None
    pin: Optional[int] = None
    username: Optional[str] = None  # For admin fallback
    password: Optional[str] = None   # For admin fallback


class LoginResponse(BaseModel):
    success: bool
    employee_id: Optional[int] = None
    first_name: str
    last_name: Optional[str] = None
    role: str
    dashboard: str


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Salary Management System API",
    version="0.1.0",
    description="Backend API for the Salary Management System (Neon + FastAPI).",
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# CORS Configuration - Restrict to specific origins in production
# Get allowed origins from environment variable, default to empty list for production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []
# In development, allow localhost; in production, use specific domains
if not ALLOWED_ORIGINS or (len(ALLOWED_ORIGINS) == 1 and not ALLOWED_ORIGINS[0]):
    # Development mode - allow common localhost ports
    ALLOWED_ORIGINS = [
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    expose_headers=["Content-Type"],
)

# Mount static files (images, videos, CSS, JS)
# Use absolute path for Vercel compatibility
# Get project root directory
# main.py is in the root, so parent is the project root
PROJECT_ROOT = Path(__file__).parent
static_dir = PROJECT_ROOT / "static"
templates_dir = PROJECT_ROOT / "templates"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ---------------------------------------------------------------------------
# Template routes (serve HTML pages)
# ---------------------------------------------------------------------------

@app.get("/", tags=["pages"])
def read_root():
    """Redirect root to login page."""
    return FileResponse(str(templates_dir / "login.html"))


@app.get("/login", tags=["pages"])
def login_page():
    """Serve login page."""
    return FileResponse(str(templates_dir / "login.html"))


@app.get("/admin-dashboard", tags=["pages"])
def admin_dashboard():
    """Serve admin dashboard."""
    return FileResponse(str(templates_dir / "admin_dashboard.html"))


@app.get("/staff-dashboard", tags=["pages"])
def staff_dashboard():
    """Serve staff dashboard."""
    return FileResponse(str(templates_dir / "staff_dashboard.html"))


@app.get("/manager-dashboard", tags=["pages"])
def manager_dashboard():
    """Serve manager dashboard."""
    return FileResponse(str(templates_dir / "manager_dashboard.html"))


@app.get("/manager-dashboard-self", tags=["pages"])
def manager_dashboard_self():
    """Serve manager self-service dashboard."""
    return FileResponse(str(templates_dir / "manager_dashboard_self.html"))


@app.get("/health", tags=["system"])
def health_check(db: Session = Depends(get_db)):
    """Simple health check & DB connectivity test."""
    db.execute(func.now())  # will raise if DB is unreachable
    return {"status": "ok", "database": "connected"}


# ---------------------------------------------------------------------------
# Employee management (Admin / Manager)
# ---------------------------------------------------------------------------

@app.post("/api/employees", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED, tags=["employees"])
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    # Ensure unique phone number
    existing = db.query(Employee).filter(Employee.phone_no == payload.phone_no).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An employee with this phone number already exists.",
        )

    try:
        role_enum = Role(payload.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'staff' or 'manager'.")

    employee = Employee(
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=role_enum,
        salary=payload.salary,
        phone_no=payload.phone_no,
        employment_start_date=payload.employment_start_date or date.today(),
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    
    # Calculate and update attendance fields
    update_employee_attendance(db, employee)
    
    return employee


@app.get("/api/employees", response_model=List[EmployeeOut], tags=["employees"])
def list_employees(db: Session = Depends(get_db)):
    qs = db.query(Employee).order_by(Employee.first_name, Employee.last_name).all()
    return qs


# ---------------------------------------------------------------------------
# User auth / PIN management (Admin)
# ---------------------------------------------------------------------------

@app.post("/api/login", response_model=LoginResponse, tags=["auth"])
@limiter.limit("5/minute")  # Rate limit: 5 login attempts per minute
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint that validates PIN and returns employee info with role-based routing.
    Accepts either:
    - first_name + pin (for regular users with PIN set in UserAuth)
    - Admin: first_name='admin' + pin=4326 OR username='admin' + password='4326'
    """
    first_name = payload.first_name.strip() if payload.first_name else ''
    pin = payload.pin
    username = payload.username.strip() if payload.username else ''
    password = payload.password.strip() if payload.password else ''
    
    # Handle None values for optional fields
    if first_name is None:
        first_name = ''
    if username is None:
        username = ''
    if password is None:
        password = ''
    
    # Admin login - support both PIN-based and username/password
    # Option 1: PIN-based (first_name='admin' and pin=4326)
    if first_name and first_name.lower() == 'admin':
        try:
            pin_value = int(pin) if pin is not None else None
            if pin_value == 4326:
                return LoginResponse(
                    success=True,
                    employee_id=None,
                    first_name="Admin",
                    last_name=None,
                    role="admin",
                    dashboard="/admin-dashboard"
                )
        except (ValueError, TypeError):
            pass  # PIN is not a valid number, continue to regular login
    
    # Option 2: Username/password fallback (username='admin' and password='4326')
    if username and username.lower() == 'admin' and password == '4326':
        return LoginResponse(
            success=True,
            employee_id=None,
            first_name="Admin",
            last_name=None,
            role="admin",
            dashboard="/admin-dashboard"
        )
    
    # PIN-based login for regular users
    if not first_name or pin is None:
        raise HTTPException(status_code=400, detail="Invalid credentials provided.")
    
    # Convert PIN to int if it's a string
    try:
        pin_int = int(pin) if isinstance(pin, str) else pin
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid credentials provided.")
    
    # Find UserAuth by first_name and PIN
    auth = db.query(UserAuth).filter(
        UserAuth.first_name == first_name,
        UserAuth.pin == pin_int
    ).first()
    
    if not auth:
        raise HTTPException(status_code=401, detail="Invalid credentials. Please check your login information.")
    
    # Find the employee by first_name (matching the one used in UserAuth)
    # Note: If multiple employees share the same first_name, we get the first match
    # In the future, UserAuth could store employee_id for better matching
    employee = db.query(Employee).filter(Employee.first_name == first_name).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")
    
    # Determine dashboard based on role
    role_value = employee.role.value if hasattr(employee.role, 'value') else str(employee.role)
    
    dashboard_map = {
        'admin': '/admin-dashboard',
        'manager': '/manager-dashboard',
        'staff': '/staff-dashboard'
    }
    
    dashboard = dashboard_map.get(role_value, '/login')
    
    return {
        "success": True,
        "employee_id": employee.id,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "role": role_value,
        "dashboard": dashboard
    }


@app.get("/api/user-auth/{employee_id}", response_model=Optional[UserAuthOut], tags=["user_auth"])
def get_user_pin(employee_id: int, db: Session = Depends(get_db)):
    """
    Retrieve the PIN for an employee by their employee_id.
    Returns None if no PIN has been set for this employee.
    """
    employee = db.query(Employee).get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    # Find UserAuth by first_name (since UserAuth uses first_name, not employee_id)
    auth = db.query(UserAuth).filter(UserAuth.first_name == employee.first_name).first()
    
    if not auth:
        return None
    
    return auth


@app.post("/api/user-auth", response_model=UserAuthOut, status_code=status.HTTP_201_CREATED, tags=["user_auth"])
def set_user_pin(payload: UserAuthCreate, db: Session = Depends(get_db)):
    """
    Assign or update a 4-digit PIN for an employee.
    The PIN is stored in the user_auth table along with the employee's first name.
    """
    employee = db.query(Employee).get(payload.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    # Enforce 4-digit PIN (0000–9999)
    if payload.pin < 0 or payload.pin > 9999:
        raise HTTPException(status_code=400, detail="PIN must be a 4-digit number between 0000 and 9999.")

    # Remove any existing auth record for this first_name (one PIN per user)
    db.query(UserAuth).filter(UserAuth.first_name == employee.first_name).delete()

    auth = UserAuth(pin=payload.pin, first_name=employee.first_name)
    db.add(auth)
    db.commit()
    db.refresh(auth)

    return auth


# ---------------------------------------------------------------------------
# Advances & Off days (Staff / Manager self‑service)
# ---------------------------------------------------------------------------

@app.post("/api/advances", status_code=status.HTTP_201_CREATED, tags=["advances"])
def create_advance(payload: AdvanceCreate, db: Session = Depends(get_db)):
    employee = db.query(Employee).get(payload.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    # Check remaining salary before allowing advance request
    remaining_salary = calculate_remaining_salary(employee.id, db)
    base_salary = float(employee.salary or 0)
    
    # Calculate what the new used amount would be (including this pending advance)
    bills_sum = (
        db.query(func.coalesce(func.sum(Bill.amount_billed), 0.0))
        .filter(Bill.billed_employee_id == employee.id)
        .scalar()
    )
    advances_sum = (
        db.query(func.coalesce(func.sum(Advance.amount_for_advance), 0.0))
        .filter(
            Advance.employee_id == employee.id,
            Advance.status == AdvanceStatus.APPROVED,
        )
        .scalar()
    )
    current_used = float(bills_sum or 0) + float(advances_sum or 0)
    new_used = current_used + payload.amount
    
    # Ensure used salary never exceeds base salary
    if new_used > base_salary:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot request advance: This would make total used salary ${new_used:.2f}, which exceeds base salary of ${base_salary:.2f}. Maximum allowed: ${remaining_salary:.2f}. Advance request automatically rejected."
        )
    
    if remaining_salary <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot request advance: You have no remaining salary (${remaining_salary:.2f}). You have already used all your base salary. Advance request automatically rejected."
        )
    
    if payload.amount > remaining_salary:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot request advance: Amount ${payload.amount:.2f} exceeds your remaining salary of ${remaining_salary:.2f}. Advance request automatically rejected."
        )

    advance = Advance(
        employee_id=employee.id,
        amount_for_advance=payload.amount,
        reason=payload.reason,
        status=AdvanceStatus.PENDING,
    )
    db.add(advance)
    db.commit()
    db.refresh(advance)
    return {"id": advance.id, "status": advance.status.value}


class AdvanceApprovalRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None


@app.put("/api/advances/{advance_id}/approve", response_model=AdvanceOut, tags=["advances"])
def approve_advance(advance_id: int, payload: AdvanceApprovalRequest, db: Session = Depends(get_db)):
    """
    Approve or reject an advance request (admin only).
    """
    advance = db.query(Advance).get(advance_id)
    if not advance:
        raise HTTPException(status_code=404, detail="Advance not found.")

    if advance.status != AdvanceStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Advance is already {advance.status.value}. Cannot change status.")

    # Get employee for response (needed for both approval and rejection)
    employee = db.query(Employee).get(advance.employee_id)
    
    if payload.approved:
        # Check remaining salary before approving advance
        remaining_salary = calculate_remaining_salary(advance.employee_id, db)
        base_salary = float(employee.salary or 0)
        
        # Calculate what the new used amount would be if we approve this advance
        bills_sum = (
            db.query(func.coalesce(func.sum(Bill.amount_billed), 0.0))
            .filter(Bill.billed_employee_id == advance.employee_id)
            .scalar()
        )
        approved_advances_sum = (
            db.query(func.coalesce(func.sum(Advance.amount_for_advance), 0.0))
            .filter(
                Advance.employee_id == advance.employee_id,
                Advance.status == AdvanceStatus.APPROVED,
            )
            .scalar()
        )
        current_used = float(bills_sum or 0) + float(approved_advances_sum or 0)
        new_used = current_used + advance.amount_for_advance
        new_remaining = base_salary - new_used
        
        # STRICT VALIDATION: Block approval if it would exceed base salary in ANY way
        # Check 1: Would total used exceed base salary? (Main check)
        if new_used > base_salary:
            advance.status = AdvanceStatus.DENIED
            advance.approved_at = datetime.utcnow()
            auto_reject_msg = f" [AUTO-REJECTED: Would make total used salary ${new_used:.2f}, exceeding base salary ${base_salary:.2f}. Remaining would be negative: ${new_remaining:.2f}]"
            advance.approval_notes = (payload.notes + auto_reject_msg) if payload.notes else auto_reject_msg.strip()
            db.commit()
            db.refresh(advance)
        # Check 2: Would remaining go negative? (Same as check 1, but explicit)
        elif new_remaining < 0:
            advance.status = AdvanceStatus.DENIED
            advance.approved_at = datetime.utcnow()
            auto_reject_msg = f" [AUTO-REJECTED: No remaining salary. Would become negative: ${new_remaining:.2f}. Current remaining: ${remaining_salary:.2f}]"
            advance.approval_notes = (payload.notes + auto_reject_msg) if payload.notes else auto_reject_msg.strip()
            db.commit()
            db.refresh(advance)
        # Check 3: Is there already no remaining salary?
        elif remaining_salary <= 0:
            advance.status = AdvanceStatus.DENIED
            advance.approved_at = datetime.utcnow()
            auto_reject_msg = f" [AUTO-REJECTED: No remaining salary available. Current remaining: ${remaining_salary:.2f}]"
            advance.approval_notes = (payload.notes + auto_reject_msg) if payload.notes else auto_reject_msg.strip()
            db.commit()
            db.refresh(advance)
        # Check 4: Does advance amount exceed remaining?
        elif advance.amount_for_advance > remaining_salary:
            advance.status = AdvanceStatus.DENIED
            advance.approved_at = datetime.utcnow()
            auto_reject_msg = f" [AUTO-REJECTED: Amount ${advance.amount_for_advance:.2f} exceeds remaining salary ${remaining_salary:.2f}]"
            advance.approval_notes = (payload.notes + auto_reject_msg) if payload.notes else auto_reject_msg.strip()
            db.commit()
            db.refresh(advance)
        else:
            # Only approve if ALL checks pass
            advance.status = AdvanceStatus.APPROVED
            advance.approved_at = datetime.utcnow()
            advance.approval_notes = payload.notes
    else:
        # Manual rejection
        advance.status = AdvanceStatus.DENIED
        advance.approved_at = datetime.utcnow()
        advance.approval_notes = payload.notes

    db.commit()
    db.refresh(advance)

    status_value = advance.status.value if hasattr(advance.status, 'value') else str(advance.status)

    return AdvanceOut(
        id=advance.id,
        employee_id=employee.id,
        employee_name=f"{employee.first_name} {employee.last_name}",
        amount_for_advance=advance.amount_for_advance,
        reason=advance.reason,
        status=status_value,
        created_at=advance.created_at,
        approved_at=advance.approved_at,
        approval_notes=advance.approval_notes,
    )


class BillCreate(BaseModel):
    manager_id: int
    employee_id: int
    amount: float = Field(..., gt=0)
    date: date
    reason: Optional[str] = None


@app.post("/api/bills", status_code=status.HTTP_201_CREATED, tags=["bills"])
def create_bill(payload: BillCreate, db: Session = Depends(get_db)):
    """
    Create a bill for a staff or manager. Only managers or admins may create bills.
    Managers cannot create bills for themselves.
    """
    manager = db.query(Employee).get(payload.manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail=f"Manager with ID {payload.manager_id} not found.")
    
    # Check role - handle both enum and string values
    role_value = manager.role.value if hasattr(manager.role, 'value') else str(manager.role)
    if role_value not in ('manager', 'admin'):
        raise HTTPException(
            status_code=403, 
            detail=f"Only managers or admins can create bills. User role is: {role_value}"
        )

    employee = db.query(Employee).get(payload.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee to bill not found.")

    # Prevent managers from billing themselves (admins may bill anyone)
    if role_value == 'manager' and manager.id == employee.id:
        raise HTTPException(status_code=400, detail="Managers cannot create bills for themselves.")

    # Check remaining salary before adding bill
    remaining_salary = calculate_remaining_salary(employee.id, db)
    base_salary = float(employee.salary or 0)
    
    # Calculate what the new used amount would be
    bills_sum = (
        db.query(func.coalesce(func.sum(Bill.amount_billed), 0.0))
        .filter(Bill.billed_employee_id == employee.id)
        .scalar()
    )
    advances_sum = (
        db.query(func.coalesce(func.sum(Advance.amount_for_advance), 0.0))
        .filter(
            Advance.employee_id == employee.id,
            Advance.status == AdvanceStatus.APPROVED,
        )
        .scalar()
    )
    current_used = float(bills_sum or 0) + float(advances_sum or 0)
    new_used = current_used + payload.amount
    
    # Ensure used salary never exceeds base salary
    if new_used > base_salary:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot add bill: This would make total used salary ${new_used:.2f}, which exceeds base salary of ${base_salary:.2f} for {employee.first_name} {employee.last_name}. Maximum allowed: ${remaining_salary:.2f}."
        )
    
    if remaining_salary <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot add bill: Employee {employee.first_name} {employee.last_name} has no remaining salary (${remaining_salary:.2f}). They have already used all their base salary."
        )
    
    if payload.amount > remaining_salary:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot add bill: Amount ${payload.amount:.2f} exceeds remaining salary of ${remaining_salary:.2f} for {employee.first_name} {employee.last_name}."
        )

    bill_datetime = (
        payload.date if isinstance(payload.date, datetime) else datetime.combine(payload.date, datetime.min.time())
    )

    bill = Bill(
        employee_id=employee.id,
        billed_employee_id=employee.id,
        amount_billed=payload.amount,
        date=bill_datetime,
        reason=payload.reason,
        recorded_by_id=manager.id,
    )

    db.add(bill)
    db.commit()
    db.refresh(bill)
    return {"id": bill.id}


@app.post("/api/off-days", status_code=status.HTTP_201_CREATED, tags=["off_days"])
def create_off_day(payload: OffDayCreate, db: Session = Depends(get_db)):
    employee = db.query(Employee).get(payload.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    off = OffDay(
        employee_id=employee.id,
        date=payload.date,
        day_count=payload.day_count,
        off_type=payload.off_type,
        reason=payload.reason,
        status=OffDayStatus.PENDING,
    )
    db.add(off)
    db.commit()
    db.refresh(off)
    return {"id": off.id, "date": off.date.isoformat()}


class OffDayApprovalRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None


@app.put("/api/off-days/{off_day_id}/approve", response_model=OffDayOut, tags=["off_days"])
def approve_off_day(off_day_id: int, payload: OffDayApprovalRequest, db: Session = Depends(get_db)):
    """
    Approve or deny an off day request (admin only).
    Updates employee attendance when status changes.
    """
    off_day = db.query(OffDay).get(off_day_id)
    if not off_day:
        raise HTTPException(status_code=404, detail="Off day request not found.")

    if off_day.status != OffDayStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Off day is already {off_day.status.value}. Cannot change status.")

    # Update status
    if payload.approved:
        off_day.status = OffDayStatus.APPROVED
    else:
        off_day.status = OffDayStatus.DENIED
    
    db.commit()
    db.refresh(off_day)

    # Update employee attendance after status change
    employee = db.query(Employee).get(off_day.employee_id)
    if employee:
        update_employee_attendance(db, employee)
        db.refresh(employee)

    status_value = off_day.status.value if hasattr(off_day.status, 'value') else str(off_day.status)
    
    return OffDayOut(
        id=off_day.id,
        employee_id=employee.id,
        employee_name=f"{employee.first_name} {employee.last_name}",
        days_worked_this_month=employee.days_worked_this_month,
        total_days_worked=employee.total_days_worked,
        date=off_day.date,
        day_count=off_day.day_count,
        off_type=off_day.off_type,
        reason=off_day.reason,
        status=status_value,
        created_at=off_day.created_at,
    )


@app.post("/api/employees/{employee_id}/refresh-attendance", tags=["employees"])
def refresh_employee_attendance(employee_id: int, db: Session = Depends(get_db)):
    """
    Manually refresh attendance calculations for an employee.
    Useful for recalculating after data changes.
    """
    employee = db.query(Employee).get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")
    
    update_employee_attendance(db, employee)
    
    return {
        "employee_id": employee.id,
        "days_worked_this_month": employee.days_worked_this_month,
        "total_days_worked": employee.total_days_worked,
    }


@app.post("/api/admin/refresh-all-attendance", tags=["employees"])
def refresh_all_attendance(db: Session = Depends(get_db)):
    """
    Refresh attendance calculations for all employees.
    Admin only endpoint.
    """
    employees = db.query(Employee).all()
    updated_count = 0
    
    for employee in employees:
        update_employee_attendance(db, employee)
        updated_count += 1
    
    return {
        "message": f"Attendance refreshed for {updated_count} employees",
        "updated_count": updated_count,
    }


# ---------------------------------------------------------------------------
# Admin / Manager views
# ---------------------------------------------------------------------------

@app.get("/api/admin/salary-summary", response_model=List[SalarySummaryItem], tags=["reports"])
def get_salary_summary(db: Session = Depends(get_db)):
    """
    For each employee, compute:
    - used_salary = sum(bills) + sum(approved advances)
    - remaining_salary = max(salary - used_salary, 0)
    """
    employees = db.query(Employee).all()
    results: List[SalarySummaryItem] = []

    for emp in employees:
        # Sum of all bills for this employee
        bills_sum = (
            db.query(func.coalesce(func.sum(Bill.amount_billed), 0.0))
            .filter(Bill.billed_employee_id == emp.id)
            .scalar()
        )

        # Sum of approved advances for this employee
        advances_sum = (
            db.query(func.coalesce(func.sum(Advance.amount_for_advance), 0.0))
            .filter(
                Advance.employee_id == emp.id,
                Advance.status == AdvanceStatus.APPROVED,
            )
            .scalar()
        )

        used = float(bills_sum or 0) + float(advances_sum or 0)
        salary = float(emp.salary or 0)
        # Calculate remaining - allow negative to show overage
        remaining = salary - used

        results.append(
            SalarySummaryItem(
                employee_id=emp.id,
                first_name=emp.first_name,
                last_name=emp.last_name,
                role=emp.role.value,
                salary=salary,
                used_salary=round(used, 2),
                remaining_salary=round(remaining, 2),
            )
        )

    return results


@app.get(
    "/api/manager/{manager_id}/recent-bills",
    response_model=List[BillOut],
    tags=["reports"],
)
def get_manager_recent_bills(manager_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """
    Return recent bills recorded by a manager (for manager dashboard).
    """
    manager = db.query(Employee).get(manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found.")

    qs = (
        db.query(Bill, Employee)
        .join(Employee, Bill.billed_employee_id == Employee.id)
        .filter(Bill.recorded_by_id == manager_id)
        .order_by(Bill.date.desc())
        .limit(limit)
        .all()
    )

    items: List[BillOut] = []
    for bill, emp in qs:
        items.append(
            BillOut(
                id=bill.id,
                date=bill.date,
                employee_id=emp.id,
                employee_name=f"{emp.first_name} {emp.last_name}",
                role=emp.role.value,
                amount=bill.amount_billed,
                reason=bill.reason,
                record_type="bill",
            )
        )

    return items


@app.get("/api/admin/advances", response_model=List[AdvanceOut], tags=["reports"])
def get_all_advances(db: Session = Depends(get_db)):
    """
    Get all advances with their status (for admin dashboard details tab).
    """
    qs = (
        db.query(Advance, Employee)
        .join(Employee, Advance.employee_id == Employee.id)
        .order_by(Advance.created_at.desc())
        .all()
    )

    items: List[AdvanceOut] = []
    for advance, emp in qs:
        status_value = advance.status.value if hasattr(advance.status, 'value') else str(advance.status)
        items.append(
            AdvanceOut(
                id=advance.id,
                employee_id=emp.id,
                employee_name=f"{emp.first_name} {emp.last_name}",
                amount_for_advance=advance.amount_for_advance,
                reason=advance.reason,
                status=status_value,
                created_at=advance.created_at,
                approved_at=advance.approved_at,
                approval_notes=advance.approval_notes,
            )
        )

    return items


@app.get("/api/admin/bills", response_model=List[BillOut], tags=["reports"])
def get_all_bills(db: Session = Depends(get_db)):
    """
    Get all bills (for admin dashboard details tab).
    """
    # Create aliases for the two employee joins
    BilledEmployee = aliased(Employee)
    RecorderEmployee = aliased(Employee)
    
    qs = (
        db.query(Bill, BilledEmployee, RecorderEmployee)
        .join(BilledEmployee, Bill.billed_employee_id == BilledEmployee.id)
        .join(RecorderEmployee, Bill.recorded_by_id == RecorderEmployee.id)
        .order_by(Bill.date.desc())
        .all()
    )

    items: List[BillOut] = []
    for bill, billed_emp, recorder_emp in qs:
        items.append(
            BillOut(
                id=bill.id,
                date=bill.date,
                employee_id=billed_emp.id,
                employee_name=f"{billed_emp.first_name} {billed_emp.last_name}",
                role=billed_emp.role.value if hasattr(billed_emp.role, 'value') else str(billed_emp.role),
                amount=bill.amount_billed,
                reason=bill.reason,
                record_type="bill",
                recorded_by_name=f"{recorder_emp.first_name} {recorder_emp.last_name}",
            )
        )

    return items


@app.get("/api/admin/off-days", response_model=List[OffDayOut], tags=["reports"])
def get_all_off_days(db: Session = Depends(get_db)):
    """
    Get all off days with employee information (for admin dashboard).
    """
    qs = (
        db.query(OffDay, Employee)
        .join(Employee, OffDay.employee_id == Employee.id)
        .order_by(OffDay.created_at.desc())
        .all()
    )

    items: List[OffDayOut] = []
    for off_day, emp in qs:
        status_value = off_day.status.value if hasattr(off_day.status, 'value') else str(off_day.status)
        items.append(
            OffDayOut(
                id=off_day.id,
                employee_id=emp.id,
                employee_name=f"{emp.first_name} {emp.last_name}",
                days_worked_this_month=emp.days_worked_this_month,
                total_days_worked=emp.total_days_worked,
                date=off_day.date,
                day_count=off_day.day_count,
                off_type=off_day.off_type,
                reason=off_day.reason,
                status=status_value,
                created_at=off_day.created_at,
            )
        )

    return items


if __name__ == "__main__":
    import uvicorn

    # Run the app directly (reload disabled due to app package name conflict)
    # For reload, use: uvicorn app:app --reload (but this conflicts with app/ package)
    # Alternative: rename app.py to main.py and use: uvicorn main:app --reload
    uvicorn.run(
        app,  # Pass app object directly
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disabled to avoid import string requirement
    )
