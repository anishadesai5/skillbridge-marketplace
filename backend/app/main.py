from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload
from app.db import get_db
from app.models import Administrator, Booking, BookingStatus, Credential, Customer, Provider, Role, ServicePackage, UserAccount
from app.schemas import BookingCreate, BookingDetailOut, BookingOut, BookingTransitionRequest, CredentialCreate, CredentialOut, HealthOut, LoginRequest, MilestoneBatchCreate, MilestoneOut, ProviderAdminOut, ProviderDecision, ProviderOut, ProviderProfileUpdate, RegisterRequest, ServiceListingOut, TokenOut, UserOut
from app.security import create_access_token, get_current_user, hash_password, require_roles, verify_password
from app.services import create_booking, publish_provider, replace_milestones, transition_booking

app=FastAPI(title="SkillBridge API",version="0.1.0",description="CS 701 prototype. All payment records are simulated.")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

@app.get("/health",response_model=HealthOut)
def health(db:Session=Depends(get_db)):
    db.execute(text("select 1"));return {"status":"ok","database":"connected","payment_mode":"simulated"}

def public_provider(provider:Provider)->ProviderOut:
    return ProviderOut(
        id=provider.id,first_name=provider.first_name,last_name=provider.last_name,
        bio=provider.bio,portfolio_url=provider.portfolio_url,rating=provider.rating,
        packages=[package for package in provider.packages if package.active],
    )

@app.get("/providers",response_model=list[ProviderOut])
def providers(category:str|None=Query(default=None),db:Session=Depends(get_db)):
    result=db.scalars(select(Provider).where(Provider.published.is_(True),Provider.status=="Approved").options(selectinload(Provider.packages))).unique().all()
    if category:result=[p for p in result if any(x.active and x.category.lower()==category.strip().lower() for x in p.packages)]
    return [public_provider(provider) for provider in result]

@app.get("/providers/{provider_id:int}",response_model=ProviderOut)
def provider_detail(provider_id:int,db:Session=Depends(get_db)):
    provider=db.scalar(select(Provider).where(Provider.id==provider_id,Provider.published.is_(True),Provider.status=="Approved").options(selectinload(Provider.packages)))
    if not provider:raise HTTPException(404,"Provider not found")
    return public_provider(provider)

@app.get("/services",response_model=list[ServiceListingOut])
def services(
    q:str|None=Query(default=None,max_length=100),
    category:str|None=Query(default=None,max_length=100),
    min_price:Decimal|None=Query(default=None,ge=0),
    max_price:Decimal|None=Query(default=None,ge=0),
    min_rating:Decimal|None=Query(default=None,ge=0,le=5),
    db:Session=Depends(get_db),
):
    if min_price is not None and max_price is not None and min_price>max_price:raise HTTPException(422,"Minimum price cannot exceed maximum price")
    statement=select(ServicePackage,Provider).join(Provider,Provider.id==ServicePackage.provider_id).where(ServicePackage.active.is_(True),Provider.published.is_(True),Provider.status=="Approved")
    if category:statement=statement.where(ServicePackage.category.ilike(category.strip()))
    if min_price is not None:statement=statement.where(ServicePackage.price>=min_price)
    if max_price is not None:statement=statement.where(ServicePackage.price<=max_price)
    if min_rating is not None:statement=statement.where(Provider.rating>=min_rating)
    rows=db.execute(statement.order_by(Provider.rating.desc(),ServicePackage.price.asc())).all()
    needle=q.strip().lower() if q else None
    listings=[]
    for package,provider in rows:
        if needle and needle not in f"{package.title} {package.description} {provider.first_name} {provider.last_name}".lower():continue
        listings.append(ServiceListingOut(package_id=package.id,provider_id=provider.id,provider_name=f"{provider.first_name} {provider.last_name}",provider_rating=provider.rating,category=package.category,title=package.title,description=package.description,price=package.price,duration_days=package.duration_days))
    return listings

@app.post("/auth/register",response_model=TokenOut,status_code=201)
def register(payload:RegisterRequest,db:Session=Depends(get_db)):
    email=payload.email.strip().lower()
    if payload.role==Role.ADMIN:raise HTTPException(403,"Administrator accounts cannot be self-registered")
    if db.scalar(select(UserAccount.id).where(UserAccount.email==email)):raise HTTPException(409,"Email is already registered")
    user=UserAccount(email=email,password_hash=hash_password(payload.password),role=payload.role)
    db.add(user);db.flush()
    if payload.role==Role.CUSTOMER:
        db.add(Customer(user_id=user.id,first_name=payload.first_name,last_name=payload.last_name))
    else:
        db.add(Provider(user_id=user.id,first_name=payload.first_name,last_name=payload.last_name,status="Pending",published=False))
    db.commit();db.refresh(user)
    return {"access_token":create_access_token(user),"user":user}

@app.post("/auth/login",response_model=TokenOut)
def login(payload:LoginRequest,db:Session=Depends(get_db)):
    user=db.scalar(select(UserAccount).where(UserAccount.email==payload.email.strip().lower()))
    if not user or not verify_password(payload.password,user.password_hash):raise HTTPException(401,"Invalid email or password")
    return {"access_token":create_access_token(user),"user":user}

@app.get("/auth/me",response_model=UserOut)
def me(user:UserAccount=Depends(get_current_user)):return user

@app.get("/providers/me",response_model=ProviderAdminOut)
def provider_me(user:UserAccount=Depends(require_roles(Role.PROVIDER)),db:Session=Depends(get_db)):
    provider=db.scalar(select(Provider).where(Provider.user_id==user.id).options(selectinload(Provider.credentials)))
    if not provider:raise HTTPException(404,"Provider profile not found")
    return provider

@app.put("/providers/me",response_model=ProviderAdminOut)
def update_provider(payload:ProviderProfileUpdate,user:UserAccount=Depends(require_roles(Role.PROVIDER)),db:Session=Depends(get_db)):
    provider=db.scalar(select(Provider).where(Provider.user_id==user.id).options(selectinload(Provider.credentials)))
    if not provider:raise HTTPException(404,"Provider profile not found")
    for field,value in payload.model_dump().items():setattr(provider,field,value)
    provider.status="Pending";provider.published=False
    db.commit();db.refresh(provider);return provider

@app.post("/providers/me/credentials",response_model=CredentialOut,status_code=201)
def add_credential(payload:CredentialCreate,user:UserAccount=Depends(require_roles(Role.PROVIDER)),db:Session=Depends(get_db)):
    provider=db.scalar(select(Provider).where(Provider.user_id==user.id))
    credential=Credential(provider_id=provider.id,credential_type=payload.credential_type,document_url=payload.document_url,status="Pending")
    provider.status="Pending";provider.published=False
    db.add(credential);db.commit();db.refresh(credential);return credential

@app.get("/admin/providers/pending",response_model=list[ProviderAdminOut])
def pending_providers(user:UserAccount=Depends(require_roles(Role.ADMIN)),db:Session=Depends(get_db)):
    return db.scalars(select(Provider).where(Provider.status=="Pending").options(selectinload(Provider.credentials))).unique().all()

@app.post("/admin/providers/{provider_id}/decision",response_model=ProviderAdminOut)
def decide_provider(provider_id:int,payload:ProviderDecision,user:UserAccount=Depends(require_roles(Role.ADMIN)),db:Session=Depends(get_db)):
    provider=db.scalar(select(Provider).where(Provider.id==provider_id).options(selectinload(Provider.credentials)))
    if not provider:raise HTTPException(404,"Provider profile not found")
    if payload.decision=="approve":
        for credential in provider.credentials:credential.status="Verified"
        db.flush()
        try:publish_provider(db,provider)
        except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    else:
        provider.status="Rejected";provider.published=False
        for credential in provider.credentials:
            if credential.status=="Pending":credential.status="Rejected"
    db.commit();db.refresh(provider);return provider

@app.post("/bookings",response_model=BookingOut,status_code=201)
def bookings(payload:BookingCreate,user:UserAccount=Depends(require_roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    customer=db.scalar(select(Customer).where(Customer.user_id==user.id))
    if not customer:raise HTTPException(404,"Customer profile not found")
    package=db.get(ServicePackage,payload.package_id)
    if not package:raise HTTPException(404,"Service package not found")
    try:booking=create_booking(db,customer.id,package,payload.booking_date,payload.customer_notes)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    db.commit();db.refresh(booking);return booking

@app.get("/customers/me/bookings",response_model=list[BookingOut])
def customer_bookings(user:UserAccount=Depends(require_roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    customer=db.scalar(select(Customer).where(Customer.user_id==user.id))
    if not customer:raise HTTPException(404,"Customer profile not found")
    return db.scalars(select(Booking).where(Booking.customer_id==customer.id).order_by(Booking.created_at.desc())).all()

def booking_with_milestones(db:Session,booking_id:int)->Booking:
    booking=db.scalar(select(Booking).where(Booking.id==booking_id).options(selectinload(Booking.milestones)))
    if not booking:raise HTTPException(404,"Booking not found")
    return booking

def authorize_booking(user:UserAccount,booking:Booking,db:Session)->None:
    if user.role==Role.ADMIN:return
    if user.role==Role.CUSTOMER:
        customer=db.scalar(select(Customer).where(Customer.user_id==user.id))
        if customer and booking.customer_id==customer.id:return
    if user.role==Role.PROVIDER:
        provider=db.scalar(select(Provider).where(Provider.user_id==user.id))
        if provider and booking.provider_id==provider.id:return
    raise HTTPException(403,"Account does not have access to this booking")

@app.get("/bookings/{booking_id}",response_model=BookingDetailOut)
def booking_detail(booking_id:int,user:UserAccount=Depends(require_roles(Role.CUSTOMER,Role.PROVIDER,Role.ADMIN)),db:Session=Depends(get_db)):
    booking=booking_with_milestones(db,booking_id)
    authorize_booking(user,booking,db)
    return booking

@app.patch("/bookings/{booking_id}/status",response_model=BookingDetailOut)
def update_booking_status(booking_id:int,payload:BookingTransitionRequest,user:UserAccount=Depends(require_roles(Role.CUSTOMER,Role.PROVIDER)),db:Session=Depends(get_db)):
    booking=booking_with_milestones(db,booking_id)
    authorize_booking(user,booking,db)
    provider_targets={BookingStatus.CONFIRMED,BookingStatus.ACTIVE,BookingStatus.COMPLETED}
    if user.role==Role.PROVIDER and payload.status not in provider_targets:
        raise HTTPException(403,"Providers may confirm, start, or complete their bookings")
    if user.role==Role.CUSTOMER and payload.status!=BookingStatus.CANCELLED:
        raise HTTPException(403,"Customers may only cancel their bookings")
    try:transition_booking(booking,payload.status)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    db.commit();db.refresh(booking);return booking

@app.put("/bookings/{booking_id}/milestones",response_model=list[MilestoneOut])
def put_booking_milestones(booking_id:int,payload:MilestoneBatchCreate,user:UserAccount=Depends(require_roles(Role.PROVIDER)),db:Session=Depends(get_db)):
    booking=booking_with_milestones(db,booking_id)
    authorize_booking(user,booking,db)
    try:milestones=replace_milestones(db,booking,[item.model_dump() for item in payload.milestones])
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    db.commit()
    for milestone in milestones:db.refresh(milestone)
    return milestones
