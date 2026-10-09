from datetime import date
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Booking, BookingStatus, Credential, Milestone, Provider, ServicePackage

ALLOWED_TRANSITIONS={BookingStatus.PENDING:{BookingStatus.CONFIRMED,BookingStatus.CANCELLED},BookingStatus.CONFIRMED:{BookingStatus.ACTIVE,BookingStatus.CANCELLED},BookingStatus.ACTIVE:{BookingStatus.COMPLETED,BookingStatus.CANCELLED},BookingStatus.COMPLETED:set(),BookingStatus.CANCELLED:set()}

def publish_provider(db:Session,provider:Provider)->Provider:
    verified=db.scalar(select(Credential.id).where(Credential.provider_id==provider.id,Credential.status=="Verified"))
    if not verified: raise ValueError("A verified credential is required before publication")
    provider.published=True;provider.status="Approved";return provider

def validate_allocations(milestones:list[Milestone])->None:
    total=sum((Decimal(m.allocation_pct) for m in milestones),Decimal("0"))
    if total!=Decimal("100"):raise ValueError("Milestone allocations must total 100 percent")

def create_booking(db:Session,customer_id:int,package:ServicePackage,booking_date:date,customer_notes:str|None=None)->Booking:
    if booking_date<date.today():raise ValueError("Booking date cannot be in the past")
    provider=db.get(Provider,package.provider_id)
    if not package.active or not provider or not provider.published:raise ValueError("Package is not bookable")
    booking=Booking(customer_id=customer_id,provider_id=package.provider_id,package_id=package.id,booking_date=booking_date,total=package.price,status=BookingStatus.PENDING,payment_held=True,customer_notes=customer_notes)
    db.add(booking);db.flush();return booking

def transition_booking(booking:Booking,new_status:BookingStatus)->None:
    if new_status not in ALLOWED_TRANSITIONS[booking.status]:raise ValueError(f"Invalid transition from {booking.status} to {new_status}")
    booking.status=new_status
