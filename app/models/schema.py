"""
Salary Management System Database Schema
Using Neon Database (PostgreSQL-compatible)
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime, date
import enum

Base = declarative_base()


class Role(enum.Enum):
    """User roles in the system"""
    STAFF = "staff"
    MANAGER = "manager"
    ADMIN = "admin"


class AdvanceStatus(enum.Enum):
    """Status for advance requests"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


class OffDayStatus(enum.Enum):
    """Status for off day requests"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


class Employee(Base):
    """Employee table with user information"""
    __tablename__ = 'employee'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum(Role), nullable=False, default=Role.STAFF)
    salary = Column(Float, nullable=False)
    phone_no = Column(String(20), nullable=False, unique=True)
    # Start of employment date, used to determine salary cycles and attendance windows
    employment_start_date = Column(Date, nullable=False, default=datetime.utcnow)
    # Computed fields: days worked in current month and total days worked
    days_worked_this_month = Column(Integer, nullable=True, default=0)
    total_days_worked = Column(Integer, nullable=True, default=0)
    # Monthly used salary: tracks amount used this month (bills + advances)
    # Can exceed salary (negative remaining) - negative balance carries forward to next month
    used_salary = Column(Float, nullable=True, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    advances = relationship("Advance", back_populates="employee")
    bills_received = relationship("Bill", foreign_keys="Bill.billed_employee_id", back_populates="billed_employee")
    bills_recorded = relationship("Bill", foreign_keys="Bill.recorded_by_id", back_populates="recorded_by")
    off_days = relationship("OffDay", back_populates="employee")
    salary_payments = relationship("SalaryPayment", foreign_keys="SalaryPayment.employee_id", back_populates="employee")
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name={self.first_name} {self.last_name}, role={self.role.value})>"


class UserAuth(Base):
    """Simple authentication table (e.g. for PIN-based or lightweight auth)."""
    __tablename__ = 'user_auth'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 4-digit integer PIN
    pin = Column(Integer, nullable=False)
    first_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UserAuth(id={self.id}, first_name={self.first_name})>"


class Bill(Base):
    """Bill table – records amounts billed for staff or managers."""
    __tablename__ = 'bill'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Employee context
    employee_id = Column(Integer, ForeignKey('employee.id'), nullable=True)
    billed_employee_id = Column(Integer, ForeignKey('employee.id'), nullable=False)

    # Amount and details
    amount_billed = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    reason = Column(Text, nullable=True)

    # Who recorded this information (manager/admin)
    recorded_by_id = Column(Integer, ForeignKey('employee.id'), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    billed_employee = relationship("Employee", foreign_keys=[billed_employee_id], back_populates="bills_received")
    recorded_by = relationship("Employee", foreign_keys=[recorded_by_id], back_populates="bills_recorded")

    def __repr__(self):
        return f"<Bill(id={self.id}, billed_employee_id={self.billed_employee_id}, amount_billed={self.amount_billed})>"


class Advance(Base):
    """Advance requests table – one row per advance request."""
    __tablename__ = 'advance'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employee.id'), nullable=False)

    amount_for_advance = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)

    status = Column(Enum(AdvanceStatus), nullable=False, default=AdvanceStatus.PENDING)
    approved_at = Column(DateTime, nullable=True)
    approval_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)  # when advance was requested
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to employee
    employee = relationship("Employee", back_populates="advances")

    def __repr__(self):
        return f"<Advance(id={self.id}, employee_id={self.employee_id}, amount={self.amount_for_advance}, status={self.status.value})>"


class OffDay(Base):
    """Off day requests for employees"""
    __tablename__ = 'off_days'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employee.id'), nullable=False)

    # Calendar date for the first off day in the request
    date = Column(Date, nullable=False)

    # Number of days requested (full days or equivalent when combined with type)
    day_count = Column(Integer, nullable=False, default=1)

    # 'full' or 'half'
    off_type = Column(String(10), nullable=False, default="full")

    # Optional reason from the staff user
    reason = Column(Text, nullable=True)

    # Status: pending / approved / denied
    status = Column(Enum(OffDayStatus), nullable=False, default=OffDayStatus.PENDING)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to employee
    employee = relationship("Employee", back_populates="off_days")

    def __repr__(self):
        return f"<OffDay(id={self.id}, employee_id={self.employee_id}, date={self.date}, day_count={self.day_count}, status={self.status.value})>"


class SalaryPayment(Base):
    """Salary payment records - tracks when salaries are paid to employees"""
    __tablename__ = 'salary_payment'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employee.id'), nullable=False)
    
    # Payment details
    amount_paid = Column(Float, nullable=False)  # Amount paid (usually remaining salary or full salary)
    payment_date = Column(Date, nullable=False, default=date.today)
    
    # Optional notes about the payment
    notes = Column(Text, nullable=True)
    
    # Who recorded this payment (admin)
    paid_by_id = Column(Integer, ForeignKey('employee.id'), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id], back_populates="salary_payments")
    paid_by = relationship("Employee", foreign_keys=[paid_by_id])
    
    def __repr__(self):
        return f"<SalaryPayment(id={self.id}, employee_id={self.employee_id}, amount_paid={self.amount_paid}, payment_date={self.payment_date})>"


def create_tables(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(engine)
    print("Tables created successfully!")


def get_engine(database_url):
    """Create and return a database engine"""
    return create_engine(database_url, echo=True)


def get_session(engine):
    """Create and return a session"""
    Session = sessionmaker(bind=engine)
    return Session()

