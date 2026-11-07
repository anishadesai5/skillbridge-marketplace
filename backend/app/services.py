from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Booking, BookingStatus, Credential, LedgerTransaction, Milestone, MilestoneStatus, Provider, ProviderAvailability, ServicePackage

ALLOWED_TRANSITIONS={BookingStatus.PENDING:{BookingStatus.CONFIRMED,BookingStatus.CANCELLED,BookingStatus.REJECTED},BookingStatus.CONFIRMED:{BookingStatus.ACTIVE,BookingStatus.CANCELLED},BookingStatus.ACTIVE:{BookingStatus.COMPLETED,BookingStatus.CANCELLED},BookingStatus.COMPLETED:set(),BookingStatus.CANCELLED:set(),BookingStatus.REJECTED:set()}

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
    calendar_entry=db.scalar(select(ProviderAvailability).where(ProviderAvailability.provider_id==package.provider_id,ProviderAvailability.availability_date==booking_date))
    if calendar_entry and not calendar_entry.available:raise ValueError("Provider is unavailable on the selected date")
    conflict=db.scalar(select(Booking.id).where(Booking.provider_id==package.provider_id,Booking.booking_date==booking_date,Booking.status.notin_([BookingStatus.CANCELLED,BookingStatus.REJECTED])))
    if conflict:raise ValueError("Provider already has a booking request on the selected date")
    booking=Booking(customer_id=customer_id,provider_id=package.provider_id,package_id=package.id,booking_date=booking_date,total=package.price,status=BookingStatus.PENDING,payment_held=True,customer_notes=customer_notes)
    db.add(booking);db.flush();return booking

def transition_booking(booking:Booking,new_status:BookingStatus)->None:
    if new_status not in ALLOWED_TRANSITIONS[booking.status]:raise ValueError(f"Invalid transition from {booking.status} to {new_status}")
    if new_status==BookingStatus.ACTIVE:
        if not booking.milestones:raise ValueError("A booking needs milestones before work can start")
        validate_allocations(booking.milestones)
    if new_status==BookingStatus.COMPLETED:
        if not booking.milestones or any(m.status!=MilestoneStatus.APPROVED for m in booking.milestones):
            raise ValueError("All milestones must be approved before completion")
    booking.status=new_status

def replace_milestones(db:Session,booking:Booking,items:list[dict])->list[Milestone]:
    if booking.status not in {BookingStatus.PENDING,BookingStatus.CONFIRMED}:
        raise ValueError("Milestones can only be changed before work starts")
    proposed=[Milestone(booking_id=booking.id,**item) for item in items]
    validate_allocations(proposed)
    booking.milestones.clear()
    db.flush()
    booking.milestones.extend(proposed)
    db.flush()
    return list(booking.milestones)

def submit_milestone(milestone:Milestone,deliverable_url:str,notes:str|None)->Milestone:
    if milestone.status not in {MilestoneStatus.PENDING,MilestoneStatus.REVISION}:
        raise ValueError("Only pending milestones or requested revisions can be submitted")
    milestone.deliverable_url=deliverable_url
    milestone.submission_notes=notes
    milestone.submission_count+=1
    milestone.submitted_at=datetime.utcnow()
    milestone.status=MilestoneStatus.SUBMITTED
    return milestone

def request_milestone_revision(milestone:Milestone,reason:str)->Milestone:
    if milestone.status!=MilestoneStatus.SUBMITTED:
        raise ValueError("A revision can only be requested for submitted work")
    milestone.revision_reason=reason
    milestone.status=MilestoneStatus.REVISION
    return milestone

def approve_milestone(db:Session,booking:Booking,milestone:Milestone,commission_rate:Decimal=Decimal("10.00"))->tuple[LedgerTransaction,bool]:
    existing=db.scalar(select(LedgerTransaction).where(LedgerTransaction.milestone_id==milestone.id,LedgerTransaction.transaction_type=="MilestoneRelease"))
    if milestone.status==MilestoneStatus.APPROVED:
        if not existing:raise ValueError("Approved milestone is missing its simulated release record")
        return existing,True
    if milestone.status!=MilestoneStatus.SUBMITTED:
        raise ValueError("Only submitted work can be approved")
    amount=(Decimal(booking.total)*Decimal(milestone.allocation_pct)/Decimal("100")).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
    commission=(amount*commission_rate/Decimal("100")).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
    ledger=existing or LedgerTransaction(booking_id=booking.id,milestone_id=milestone.id,provider_id=booking.provider_id,customer_id=booking.customer_id,transaction_type="MilestoneRelease",amount=amount,commission_amount=commission,payout_amount=amount-commission,status="SimulatedReleased")
    if not existing:db.add(ledger)
    milestone.status=MilestoneStatus.APPROVED
    milestone.approved_at=datetime.utcnow()
    db.flush()
    return ledger,False
