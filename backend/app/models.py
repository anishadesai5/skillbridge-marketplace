import enum
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class Role(str, enum.Enum): CUSTOMER="customer"; PROVIDER="provider"; ADMIN="administrator"
class BookingStatus(str, enum.Enum): PENDING="Pending"; CONFIRMED="Confirmed"; ACTIVE="Active"; COMPLETED="Completed"; CANCELLED="Cancelled"
class MilestoneStatus(str, enum.Enum): PENDING="Pending"; SUBMITTED="Submitted"; REVISION="RevisionReq"; DISPUTED="Disputed"; APPROVED="Approved"

class UserAccount(Base):
    __tablename__="user_account"
    id: Mapped[int]=mapped_column(primary_key=True)
    email: Mapped[str]=mapped_column(String(255),unique=True,index=True)
    password_hash: Mapped[str]=mapped_column(String(255))
    role: Mapped[Role]=mapped_column(Enum(Role))
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)

class Provider(Base):
    __tablename__="provider"; __table_args__=(CheckConstraint("rating >= 0 AND rating <= 5",name="ck_provider_rating"),)
    id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("user_account.id"),unique=True)
    first_name: Mapped[str]=mapped_column(String(100)); last_name: Mapped[str]=mapped_column(String(100))
    status: Mapped[str]=mapped_column(String(30),default="Pending"); bio: Mapped[str|None]=mapped_column(Text)
    portfolio_url: Mapped[str|None]=mapped_column(String(500)); rating: Mapped[Decimal]=mapped_column(Numeric(2,1),default=0)
    published: Mapped[bool]=mapped_column(Boolean,default=False)
    credentials=relationship("Credential",cascade="all, delete-orphan"); packages=relationship("ServicePackage",cascade="all, delete-orphan")

class Credential(Base):
    __tablename__="credential"
    id: Mapped[int]=mapped_column(primary_key=True); provider_id: Mapped[int]=mapped_column(ForeignKey("provider.id"))
    credential_type: Mapped[str]=mapped_column(String(100)); document_url: Mapped[str]=mapped_column(String(500)); status: Mapped[str]=mapped_column(String(30),default="Pending")

class ServicePackage(Base):
    __tablename__="service_package"; __table_args__=(CheckConstraint("price > 0",name="ck_package_price_positive"),)
    id: Mapped[int]=mapped_column(primary_key=True); provider_id: Mapped[int]=mapped_column(ForeignKey("provider.id"))
    category: Mapped[str]=mapped_column(String(100),index=True); title: Mapped[str]=mapped_column(String(160)); description: Mapped[str]=mapped_column(Text)
    price: Mapped[Decimal]=mapped_column(Numeric(12,2)); duration_days: Mapped[int]=mapped_column(default=1); active: Mapped[bool]=mapped_column(Boolean,default=True)

class Customer(Base):
    __tablename__="customer"
    id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey("user_account.id"),unique=True)
    first_name: Mapped[str]=mapped_column(String(100)); last_name: Mapped[str]=mapped_column(String(100)); phone: Mapped[str|None]=mapped_column(String(30)); status: Mapped[str]=mapped_column(String(30),default="Active")

class Booking(Base):
    __tablename__="booking"; __table_args__=(CheckConstraint("total > 0",name="ck_booking_total_positive"),)
    id: Mapped[int]=mapped_column(primary_key=True); customer_id: Mapped[int]=mapped_column(ForeignKey("customer.id")); provider_id: Mapped[int]=mapped_column(ForeignKey("provider.id")); package_id: Mapped[int]=mapped_column(ForeignKey("service_package.id"))
    status: Mapped[BookingStatus]=mapped_column(Enum(BookingStatus),default=BookingStatus.PENDING); booking_date: Mapped[date]=mapped_column(Date); payment_held: Mapped[bool]=mapped_column(Boolean,default=True); total: Mapped[Decimal]=mapped_column(Numeric(12,2))
    customer_notes: Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    milestones=relationship("Milestone",cascade="all, delete-orphan")

class Milestone(Base):
    __tablename__="milestone"; __table_args__=(UniqueConstraint("booking_id","sequence",name="uq_milestone_booking_sequence"),CheckConstraint("allocation_pct > 0 AND allocation_pct <= 100",name="ck_milestone_allocation"))
    id: Mapped[int]=mapped_column(primary_key=True); booking_id: Mapped[int]=mapped_column(ForeignKey("booking.id")); sequence: Mapped[int]=mapped_column(); description: Mapped[str]=mapped_column(Text)
    status: Mapped[MilestoneStatus]=mapped_column(Enum(MilestoneStatus),default=MilestoneStatus.PENDING); deliverable_url: Mapped[str|None]=mapped_column(String(500)); submitted_at: Mapped[datetime|None]=mapped_column(DateTime); approved_at: Mapped[datetime|None]=mapped_column(DateTime); allocation_pct: Mapped[Decimal]=mapped_column(Numeric(5,2))

class LedgerTransaction(Base):
    __tablename__="ledger_transaction"; __table_args__=(CheckConstraint("amount >= 0 AND commission_amount >= 0 AND payout_amount >= 0",name="ck_ledger_nonnegative"),CheckConstraint("payout_amount = amount - commission_amount",name="ck_ledger_reconciles"),UniqueConstraint("milestone_id","transaction_type",name="uq_milestone_transaction_type"))
    id: Mapped[int]=mapped_column(primary_key=True); booking_id: Mapped[int]=mapped_column(ForeignKey("booking.id")); milestone_id: Mapped[int|None]=mapped_column(ForeignKey("milestone.id"),nullable=True); provider_id: Mapped[int]=mapped_column(ForeignKey("provider.id")); customer_id: Mapped[int]=mapped_column(ForeignKey("customer.id"))
    transaction_type: Mapped[str]=mapped_column(String(30)); amount: Mapped[Decimal]=mapped_column(Numeric(12,2)); commission_amount: Mapped[Decimal]=mapped_column(Numeric(12,2)); payout_amount: Mapped[Decimal]=mapped_column(Numeric(12,2)); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); status: Mapped[str]=mapped_column(String(30),default="Simulated")

class Administrator(Base):
    __tablename__="administrator"
    id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey("user_account.id"),unique=True); name: Mapped[str]=mapped_column(String(150)); admin_role: Mapped[str]=mapped_column(String(50),default="PlatformAdmin")

class Dispute(Base):
    __tablename__="dispute"
    id: Mapped[int]=mapped_column(primary_key=True); milestone_id: Mapped[int]=mapped_column(ForeignKey("milestone.id")); administrator_id: Mapped[int|None]=mapped_column(ForeignKey("administrator.id"),nullable=True); reason: Mapped[str]=mapped_column(Text); status: Mapped[str]=mapped_column(String(30),default="Open"); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); resolution: Mapped[str|None]=mapped_column(Text)

class CommissionRule(Base):
    __tablename__="commission_rule"; __table_args__=(CheckConstraint("rate > 0 AND rate < 100",name="ck_commission_rate"),)
    id: Mapped[int]=mapped_column(primary_key=True); administrator_id: Mapped[int]=mapped_column(ForeignKey("administrator.id")); rate: Mapped[Decimal]=mapped_column(Numeric(5,2)); effective_date: Mapped[date]=mapped_column(Date); category: Mapped[str|None]=mapped_column(String(100))

class AdminAuditLog(Base):
    __tablename__="admin_audit_log"
    id: Mapped[int]=mapped_column(primary_key=True); administrator_id: Mapped[int]=mapped_column(ForeignKey("administrator.id")); action: Mapped[str]=mapped_column(String(120)); target: Mapped[str]=mapped_column(String(160)); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); outcome: Mapped[str]=mapped_column(String(80))
