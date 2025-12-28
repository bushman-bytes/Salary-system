from datetime import date, datetime
from typing import List, Optional, Literal, Dict, Any
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
    SalaryPayment,
)
from app.utils.attendance import update_employee_attendance
from app.services.salary_payment_service import (
    record_salary_payment,
    get_employee_salary_payments,
    get_all_salary_payments,
)


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
    Returns: remaining_salary = salary - used_salary (can be negative)
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
    remaining = salary - used  # Allow negative values
    
    return remaining


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class EmployeeBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    role: Literal["staff", "manager", "admin"]
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
        if isinstance(v, str):
            return v.lower()
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
# AI Agent Request/Response Models
# ---------------------------------------------------------------------------

class SummarizeRequest(BaseModel):
    """Request model for AI summarize endpoint."""
    query_type: Literal["employee", "department", "time_period", "status"] = Field(
        ..., description="Type of summary to generate"
    )
    employee_id: Optional[int] = Field(None, description="Employee ID (for employee summary)")
    employee_name: Optional[str] = Field(None, description="Employee name (for employee summary)")
    date_range_start: Optional[date] = Field(None, description="Start date for time period")
    date_range_end: Optional[date] = Field(None, description="End date for time period")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")


class ReportRequest(BaseModel):
    """Request model for AI report endpoint."""
    report_type: Literal["financial", "operational", "analytical"] = Field(
        ..., description="Type of report to generate"
    )
    date_range_start: Optional[date] = Field(None, description="Start date for report")
    date_range_end: Optional[date] = Field(None, description="End date for report")
    employee_id: Optional[int] = Field(None, description="Optional employee filter")
    include_charts: bool = Field(False, description="Include chart data in response")


class QueryRequest(BaseModel):
    """Request model for natural language query endpoint."""
    query: str = Field(..., min_length=1, description="Natural language question or query")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")


class AIResponse(BaseModel):
    """Base response model for AI endpoints."""
    success: bool
    result: Any = Field(..., description="AI-generated result")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata about the generation")
    error: Optional[str] = Field(None, description="Error message if generation failed")


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


@app.get("/agent-dashboard", tags=["pages"])
def agent_dashboard():
    """Serve AI agent testing dashboard."""
    return FileResponse(str(templates_dir / "agent_dashboard.html"))


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
    try:
        qs = db.query(Employee).order_by(Employee.first_name, Employee.last_name).all()
        
        # Manually convert to EmployeeOut instances to ensure role is properly serialized
        result = []
        for emp in qs:
            # Convert role enum to string
            role_value = emp.role.value if hasattr(emp.role, 'value') else str(emp.role)
            
            # Create EmployeeOut instance with converted role
            employee_out = EmployeeOut(
                id=emp.id,
                first_name=emp.first_name,
                last_name=emp.last_name,
                role=role_value,  # Already converted to string
                salary=float(emp.salary),
                phone_no=emp.phone_no,
                employment_start_date=emp.employment_start_date,
                days_worked_this_month=emp.days_worked_this_month,
                total_days_worked=emp.total_days_worked,
            )
            result.append(employee_out)
        
        return result
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in list_employees: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Error loading employees: {str(e)}"
        )


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
            detail=f"Cannot request advance: This would make total used salary KSH {new_used:,.2f}, which exceeds base salary of KSH {base_salary:,.2f}. Maximum allowed: KSH {remaining_salary:,.2f}. Advance request automatically rejected."
        )
    
    if remaining_salary <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot request advance: You have no remaining salary (${remaining_salary:.2f}). You have already used all your base salary. Advance request automatically rejected."
        )
    
    if payload.amount > remaining_salary:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot request advance: Amount KSH {payload.amount:,.2f} exceeds your remaining salary of KSH {remaining_salary:,.2f}. Advance request automatically rejected."
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
            auto_reject_msg = f" [AUTO-REJECTED: Would make total used salary KSH {new_used:,.2f}, exceeding base salary KSH {base_salary:,.2f}. Remaining would be negative: KSH {new_remaining:,.2f}]"
            advance.approval_notes = (payload.notes + auto_reject_msg) if payload.notes else auto_reject_msg.strip()
            db.commit()
            db.refresh(advance)
        # Check 2: Would remaining go negative? (Same as check 1, but explicit)
        elif new_remaining < 0:
            advance.status = AdvanceStatus.DENIED
            advance.approved_at = datetime.utcnow()
            auto_reject_msg = f" [AUTO-REJECTED: No remaining salary. Would become negative: KSH {new_remaining:,.2f}. Current remaining: KSH {remaining_salary:,.2f}]"
            advance.approval_notes = (payload.notes + auto_reject_msg) if payload.notes else auto_reject_msg.strip()
            db.commit()
            db.refresh(advance)
        # Check 3: Is there already no remaining salary?
        elif remaining_salary <= 0:
            advance.status = AdvanceStatus.DENIED
            advance.approved_at = datetime.utcnow()
            auto_reject_msg = f" [AUTO-REJECTED: No remaining salary available. Current remaining: KSH {remaining_salary:,.2f}]"
            advance.approval_notes = (payload.notes + auto_reject_msg) if payload.notes else auto_reject_msg.strip()
            db.commit()
            db.refresh(advance)
        # Check 4: Does advance amount exceed remaining?
        elif advance.amount_for_advance > remaining_salary:
            advance.status = AdvanceStatus.DENIED
            advance.approved_at = datetime.utcnow()
            auto_reject_msg = f" [AUTO-REJECTED: Amount KSH {advance.amount_for_advance:,.2f} exceeds remaining salary KSH {remaining_salary:,.2f}]"
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

    # Check remaining salary before adding bill (for warning purposes)
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
    new_remaining = base_salary - new_used
    
    # Allow bills even if they exceed salary, but we'll return a warning in the response

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
    
    # Prepare response with warning if salary is exceeded
    response = {"id": bill.id}
    if new_remaining < 0:
        response["warning"] = f"⚠️ WARNING: {employee.first_name} {employee.last_name} has exceeded their salary. Remaining salary: KSH {new_remaining:,.2f} (negative). Total used: KSH {new_used:,.2f} out of base salary: KSH {base_salary:,.2f}."
    
    return response


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


# ---------------------------------------------------------------------------
# Salary Payments
# ---------------------------------------------------------------------------

class SalaryPaymentCreate(BaseModel):
    employee_id: int
    admin_id: int
    amount_paid: Optional[float] = None  # If not provided, pays remaining salary
    payment_date: Optional[date] = None
    notes: Optional[str] = None


class SalaryPaymentOut(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    amount_paid: float
    payment_date: date
    notes: Optional[str] = None
    paid_by_id: int
    paid_by_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@app.post("/api/salary-payments", status_code=status.HTTP_201_CREATED, tags=["salary_payments"])
def create_salary_payment(payload: SalaryPaymentCreate, db: Session = Depends(get_db)):
    """
    Record a salary payment for an employee (admin only).
    When salary is paid, resets used_salary to 0 (clearing the balance).
    """
    try:
        payment = record_salary_payment(
            db=db,
            employee_id=payload.employee_id,
            admin_id=payload.admin_id,
            amount_paid=payload.amount_paid,
            payment_date=payload.payment_date,
            notes=payload.notes
        )
        
        employee = db.query(Employee).get(payload.employee_id)
        admin = db.query(Employee).get(payload.admin_id)
        
        return SalaryPaymentOut(
            id=payment.id,
            employee_id=payment.employee_id,
            employee_name=f"{employee.first_name} {employee.last_name}",
            amount_paid=payment.amount_paid,
            payment_date=payment.payment_date,
            notes=payment.notes,
            paid_by_id=payment.paid_by_id,
            paid_by_name=f"{admin.first_name} {admin.last_name}",
            created_at=payment.created_at
        )
    except ValueError as e:
        print(f"ValueError in create_salary_payment: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        print(f"PermissionError in create_salary_payment: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Unexpected error in create_salary_payment: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error recording salary payment: {str(e)}")


@app.get("/api/salary-payments", response_model=List[SalaryPaymentOut], tags=["salary_payments"])
def get_salary_payments(db: Session = Depends(get_db)):
    """
    Get all salary payment records (admin only).
    """
    payments = get_all_salary_payments(db)
    
    results = []
    for payment in payments:
        employee = db.query(Employee).get(payment.employee_id)
        admin = db.query(Employee).get(payment.paid_by_id)
        
        results.append(SalaryPaymentOut(
            id=payment.id,
            employee_id=payment.employee_id,
            employee_name=f"{employee.first_name} {employee.last_name}" if employee else "Unknown",
            amount_paid=payment.amount_paid,
            payment_date=payment.payment_date,
            notes=payment.notes,
            paid_by_id=payment.paid_by_id,
            paid_by_name=f"{admin.first_name} {admin.last_name}" if admin else "Unknown",
            created_at=payment.created_at
        ))
    
    return results


@app.get("/api/salary-payments/employee/{employee_id}", response_model=List[SalaryPaymentOut], tags=["salary_payments"])
def get_employee_salary_payments_api(employee_id: int, db: Session = Depends(get_db)):
    """
    Get all salary payment records for a specific employee.
    """
    employee = db.query(Employee).get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")
    
    payments = get_employee_salary_payments(db, employee_id)
    
    results = []
    for payment in payments:
        admin = db.query(Employee).get(payment.paid_by_id)
        
        results.append(SalaryPaymentOut(
            id=payment.id,
            employee_id=payment.employee_id,
            employee_name=f"{employee.first_name} {employee.last_name}",
            amount_paid=payment.amount_paid,
            payment_date=payment.payment_date,
            notes=payment.notes,
            paid_by_id=payment.paid_by_id,
            paid_by_name=f"{admin.first_name} {admin.last_name}" if admin else "Unknown",
            created_at=payment.created_at
        ))
    
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


# ---------------------------------------------------------------------------
# AI Agent Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/ai/summarize", response_model=AIResponse, tags=["ai"])
@limiter.limit("10/minute")  # Rate limit AI endpoints
def ai_summarize(
    request: Request,
    payload: SummarizeRequest,
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered summary based on query type.
    
    Supported query types:
    - employee: Summary for a specific employee
    - department: Aggregate statistics for a department
    - time_period: Summary for a specific time period
    - status: Summary of pending/completed transactions
    """
    try:
        from app.ai_agent.report_generator import ReportGenerator
        
        # Initialize report generator
        generator = ReportGenerator(db)
        
        # Handle different query types
        if payload.query_type == "employee":
            # Build date range tuple if provided
            date_range = None
            if payload.date_range_start and payload.date_range_end:
                date_range = (payload.date_range_start, payload.date_range_end)
            
            result = generator.generate_employee_summary(
                employee_id=payload.employee_id,
                employee_name=payload.employee_name,
                date_range=date_range,
            )
            
            if "error" in result:
                return AIResponse(
                    success=False,
                    result=None,
                    error=result.get("error", "Failed to generate summary"),
                    metadata=result.get("metadata", {})
                )
            
            return AIResponse(
                success=True,
                result=result.get("summary"),
                metadata=result.get("metadata", {}),
            )
        
        elif payload.query_type == "time_period":
            # Generate financial report for time period
            date_range = None
            if payload.date_range_start and payload.date_range_end:
                date_range = (payload.date_range_start, payload.date_range_end)
            
            result = generator.generate_financial_report(
                date_range=date_range,
                employee_id=payload.employee_id,
            )
            
            if "error" in result:
                return AIResponse(
                    success=False,
                    result=None,
                    error=result.get("error", "Failed to generate summary"),
                    metadata=result.get("metadata", {})
                )
            
            return AIResponse(
                success=True,
                result=result.get("report"),
                metadata=result.get("metadata", {}),
            )
        
        else:
            return AIResponse(
                success=False,
                result=None,
                error=f"Query type '{payload.query_type}' not yet implemented",
            )
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return AIResponse(
            success=False,
            result=None,
            error=f"Error generating summary: {error_msg}",
        )


@app.post("/api/ai/report", response_model=AIResponse, tags=["ai"])
@limiter.limit("10/minute")  # Rate limit AI endpoints
def ai_report(
    request: Request,
    payload: ReportRequest,
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered comprehensive report.
    
    Supported report types:
    - financial: Financial analysis with trends
    - operational: Operational metrics and workflow status
    - analytical: Trend analysis and anomaly detection
    """
    try:
        from app.ai_agent.report_generator import ReportGenerator
        
        # Initialize report generator
        generator = ReportGenerator(db)
        
        # Build date range tuple if provided
        date_range = None
        if payload.date_range_start and payload.date_range_end:
            date_range = (payload.date_range_start, payload.date_range_end)
        
        if payload.report_type == "financial":
            result = generator.generate_financial_report(
                date_range=date_range,
                employee_id=payload.employee_id,
            )
            
            if "error" in result:
                return AIResponse(
                    success=False,
                    result=None,
                    error=result.get("error", "Failed to generate report"),
                    metadata=result.get("metadata", {})
                )
            
            return AIResponse(
                success=True,
                result=result.get("report"),
                metadata={
                    **result.get("metadata", {}),
                    "include_charts": payload.include_charts,
                },
            )
        
        else:
            return AIResponse(
                success=False,
                result=None,
                error=f"Report type '{payload.report_type}' not yet implemented",
            )
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return AIResponse(
            success=False,
            result=None,
            error=f"Error generating report: {error_msg}",
        )


@app.post("/api/ai/query", response_model=AIResponse, tags=["ai"])
@limiter.limit("20/minute")  # Higher limit for natural language queries
def ai_query(
    request: Request,
    payload: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Natural language query interface for the AI agent.
    
    Ask questions in natural language and get AI-powered responses
    with relevant data from the database.
    
    Examples:
    - "What is the total amount of pending advances?"
    - "Show me a summary for employee John Doe"
    - "Generate a financial report for last month"
    """
    try:
        from app.ai_agent.rag_engine import get_rag_engine
        from app.ai_agent.chains import get_rag_chain
        from app.ai_agent.query_processor import QueryProcessor
        
        # Initialize components
        rag_engine = get_rag_engine()
        rag_chain = get_rag_chain()
        query_processor = QueryProcessor(db)
        
        # Retrieve relevant context from knowledge base
        context_docs = rag_engine.retrieve_context(payload.query)
        retrieved_context = rag_engine.format_context(context_docs)
        
        # Try to extract structured information from query
        # This is a simple implementation - could be enhanced with NLP
        query_lower = payload.query.lower()
        
        # Check if query is asking for employee data
        employee_id = None
        employee_name = None
        if "employee" in query_lower:
            # Try to extract employee name or ID from context
            if payload.context:
                employee_id = payload.context.get("employee_id")
                employee_name = payload.context.get("employee_name")
        
        # Get relevant data if needed
        query_data = ""
        if employee_id or employee_name:
            try:
                employee_data = query_processor.get_employee_data(
                    employee_id=employee_id,
                    employee_name=employee_name,
                )
                if "error" not in employee_data:
                    import json
                    query_data = json.dumps(employee_data, indent=2)
            except:
                pass
        
        # Generate response using RAG chain
        response = rag_chain.invoke(
            query=payload.query,
            context=retrieved_context,
            query_data=query_data,
        )
        
        return AIResponse(
            success=True,
            result=response,
            metadata={
                "query": payload.query,
                "context_used": len(context_docs) > 0,
                "context_docs_count": len(context_docs),
            },
        )
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return AIResponse(
            success=False,
            result=None,
            error=f"Error processing query: {error_msg}",
        )


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
