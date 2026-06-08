from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'school.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(
    f'sqlite:///{DB_PATH}',
    connect_args={'check_same_thread': False},
    echo=False
)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    full_name = Column(String(100))
    email = Column(String(100))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)


class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    photo = Column(String(255))
    gender = Column(String(10))
    birth_date = Column(Date)
    address = Column(Text)
    parent_name = Column(String(100))
    parent_phone = Column(String(20))
    emergency_phone = Column(String(20))
    class_name = Column(String(20))
    registration_date = Column(Date, default=datetime.today)
    # Transport: 0 = No transport (NA), positive number = transport fee
    transport_fee = Column(Float, default=0.0)  # 0 means no transport
    has_transport = Column(Boolean, default=False)
    # Insurance
    insurance_amount = Column(Float, default=0.0)
    insurance_paid = Column(Boolean, default=False)
    # Monthly fee
    monthly_fee = Column(Float, default=0.0)
    # Re-inscription
    reinscription_status = Column(String(20), default='pending')  # yes / no / pending
    notes = Column(Text)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)

    payments = relationship('Payment', back_populates='student', cascade='all, delete-orphan')
    month_records = relationship('MonthRecord', back_populates='student', cascade='all, delete-orphan')


class MonthRecord(Base):
    """Stores the status of each month for each student.
    status: 'paid' | 'unpaid' | 'nan' (not inscribed that month)
    """
    __tablename__ = 'month_records'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    month_name = Column(String(20), nullable=False)   # 'Septembre', 'Octobre', …
    school_year = Column(String(10), default='2024-25')
    status = Column(String(10), default='unpaid')     # paid | unpaid | nan
    amount = Column(Float, default=0.0)               # amount for this month

    student = relationship('Student', back_populates='month_records')


class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    payment_type = Column(String(20))   # monthly | insurance | transport | inscription
    amount = Column(Float)
    month = Column(String(20))
    year = Column(Integer)
    school_year = Column(String(10), default='2024-25')  # e.g. '2024-25'
    payment_date = Column(DateTime, default=datetime.now)
    receipt_number = Column(String(30))
    notes = Column(Text)
    student = relationship('Student', back_populates='payments')


class Receipt(Base):
    __tablename__ = 'receipts'
    id = Column(Integer, primary_key=True)
    receipt_number = Column(String(30), unique=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    payment_id = Column(Integer, ForeignKey('payments.id'))
    amount = Column(Float)
    payment_type = Column(String(20))
    generated_at = Column(DateTime, default=datetime.now)
    pdf_path = Column(String(255))


class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    cin = Column(String(20))          # v4: national ID
    role = Column(String(50))
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    hire_date = Column(Date)
    base_salary = Column(Float, default=0.0)
    active = Column(Boolean, default=True)
    salaries = relationship('Salary', back_populates='employee')


class Salary(Base):
    """
    v4 Salary model:
      net_salary = gross_salary + bonus - deduction
      One salary per employee per month (duplicate prevention enforced in UI).
    """
    __tablename__ = 'salaries'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'))
    month = Column(String(20))
    year = Column(Integer)
    # v4 fields
    gross_salary = Column(Float, default=0.0)
    bonus = Column(Float, default=0.0)
    deduction = Column(Float, default=0.0)
    net_salary = Column(Float, default=0.0)   # = gross + bonus - deduction
    payment_date = Column(DateTime)
    receipt_number = Column(String(30))
    notes = Column(Text)
    # backward compat aliases
    base_amount = Column(Float, default=0.0)  # kept for old data
    total = Column(Float, default=0.0)        # kept for old data
    paid = Column(Boolean, default=True)
    paid_date = Column(DateTime)
    employee = relationship('Employee', back_populates='salaries')


class Expense(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    category = Column(String(50))
    description = Column(Text)
    amount = Column(Float)
    expense_type = Column(String(20))   # 'fixed' | 'variable'
    date = Column(Date, default=datetime.today)
    paid_by = Column(String(100))
    notes = Column(Text)


# ── v4 Expense Management ─────────────────────────────────────────────────────

class ExpenseCategory(Base):
    """
    Configured once per category (Loyer, Électricité, Eau, etc.).
    monthly_amount = expected monthly cost.
    """
    __tablename__ = 'expense_categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    expense_type = Column(String(20), default='fixed')   # 'fixed' | 'variable'
    monthly_amount = Column(Float, default=0.0)
    active = Column(Boolean, default=True)
    notes = Column(Text)
    payments = relationship('ExpensePayment', back_populates='category',
                            cascade='all, delete-orphan')


class ExpensePayment(Base):
    """
    One record per (category × month × year) payment.
    Duplicate prevention: category_id + month + year must be unique.
    """
    __tablename__ = 'expense_payments'
    id = Column(Integer, primary_key=True)
    expense_category_id = Column(Integer, ForeignKey('expense_categories.id'))
    month = Column(String(20))
    year = Column(Integer)
    amount = Column(Float)
    payment_date = Column(DateTime, default=datetime.now)
    notes = Column(Text)
    category = relationship('ExpenseCategory', back_populates='payments')


class Bus(Base):
    __tablename__ = 'buses'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    plate = Column(String(20))
    capacity = Column(Integer)
    driver_id = Column(Integer, ForeignKey('employees.id'))
    route = Column(Text)
    active = Column(Boolean, default=True)


class Schedule(Base):
    __tablename__ = 'schedules'
    id = Column(Integer, primary_key=True)
    class_name = Column(String(20))
    day = Column(String(20))
    time_start = Column(String(10))
    time_end = Column(String(10))
    subject = Column(String(50))
    teacher_id = Column(Integer, ForeignKey('employees.id'))
    room = Column(String(20))


class Setting(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True)
    value = Column(Text)


SCHOOL_MONTHS = [
    'Septembre', 'Octobre', 'Novembre', 'Décembre',
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin'
]


def get_session():
    return Session()


def init_db():
    Base.metadata.create_all(engine)
    session = Session()

    if not session.query(User).filter_by(username='admin').first():
        import hashlib
        users = [
            User(username='admin', password=hashlib.sha256('admin123'.encode()).hexdigest(),
                 role='admin', full_name='Administrateur'),
            User(username='comptable', password=hashlib.sha256('compta123'.encode()).hexdigest(),
                 role='comptable', full_name='Comptable'),
            User(username='secretaire', password=hashlib.sha256('secr123'.encode()).hexdigest(),
                 role='secretaire', full_name='Secrétaire'),
        ]
        session.add_all(users)

        defaults = [
            Setting(key='school_name', value='Le Schéma'),
            Setting(key='school_address', value='Votre adresse'),
            Setting(key='school_phone', value=''),
            Setting(key='insurance_amount', value='500'),
            Setting(key='transport_default', value='200'),
            Setting(key='school_year', value='2024-25'),
        ]
        session.add_all(defaults)
        session.commit()
    session.close()


def migrate_db():
    """Add new columns to existing DB without losing data."""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    def add_col(table, col, col_type, default='NULL'):
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type} DEFAULT {default}")
            print(f"  ✅ Added {table}.{col}")
        except sqlite3.OperationalError:
            pass  # column already exists

    add_col('students', 'transport_fee', 'REAL', '0.0')
    add_col('students', 'has_transport', 'INTEGER', '0')
    add_col('students', 'insurance_amount', 'REAL', '0.0')
    add_col('students', 'reinscription_status', "TEXT", "'pending'")
    add_col('students', 'updated_at', 'TEXT', 'NULL')
    add_col('students', 'created_at', 'TEXT', 'NULL')
    add_col('students', 'insurance_paid', 'INTEGER', '0')
    add_col('students', 'monthly_fee', 'REAL', '0.0')
    add_col('students', 'notes', 'TEXT', 'NULL')
    add_col('students', 'photo', 'TEXT', 'NULL')
    add_col('students', 'active', 'INTEGER', '1')

    # v4 additions
    add_col('payments',   'school_year',   'TEXT',  "'2024-25'")
    add_col('employees',  'cin',           'TEXT',  'NULL')
    add_col('salaries',   'gross_salary',  'REAL',  '0.0')
    add_col('salaries',   'deduction',     'REAL',  '0.0')
    add_col('salaries',   'net_salary',    'REAL',  '0.0')
    add_col('salaries',   'payment_date',  'TEXT',  'NULL')
    add_col('salaries',   'receipt_number','TEXT',  'NULL')

    # v4 new tables — created by create_all, no add_col needed
    # Seed default ExpenseCategories if table is empty
    try:
        from sqlalchemy.orm import Session as SASession
        with SASession(engine) as seed_session:
            count = seed_session.query(ExpenseCategory).count()
            if count == 0:
                defaults = [
                    ('Loyer',          'fixed',    0.0),
                    ('Électricité',    'fixed',    0.0),
                    ('Eau',            'fixed',    0.0),
                    ('Internet',       'fixed',    0.0),
                    ('Sécurité',       'fixed',    0.0),
                    ('Nettoyage',      'fixed',    0.0),
                    ('Maintenance',    'variable', 0.0),
                    ('Fournitures',    'variable', 0.0),
                    ('Autres',         'variable', 0.0),
                ]
                for name, etype, amt in defaults:
                    seed_session.add(ExpenseCategory(
                        name=name, expense_type=etype,
                        monthly_amount=amt, active=True
                    ))
                seed_session.commit()
    except Exception as e:
        print(f'Seed categories warning: {e}')

    conn.commit()
    conn.close()

    # Create new tables
    Base.metadata.create_all(engine)
    print("  ✅ New tables created")
