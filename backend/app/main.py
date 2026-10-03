from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload
from app.db import get_db
from app.models import Administrator, Credential, Customer, Provider, Role, ServicePackage, UserAccount
from app.schemas import BookingCreate, BookingOut, CredentialCreate, CredentialOut, HealthOut, LoginRequest, ProviderAdminOut, ProviderDecision, ProviderOut, ProviderProfileUpdate, RegisterRequest, TokenOut, UserOut
from app.security import create_access_token, get_current_user, hash_password, require_roles, verify_password
from app.services import create_booking, publish_provider

app=FastAPI(title="SkillBridge API",version="0.1.0",description="CS 701 prototype. All payment records are simulated.")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

@app.get("/health",response_model=HealthOut)
def health(db:Session=Depends(get_db)):
    db.execute(text("select 1"));return {"status":"ok","database":"connected","payment_mode":"simulated"}

@app.get("/providers",response_model=list[ProviderOut])
def providers(category:str|None=Query(default=None),db:Session=Depends(get_db)):
    result=db.scalars(select(Provider).where(Provider.published.is_(True)).options(selectinload(Provider.packages))).unique().all()
    if category:result=[p for p in result if any(x.active and x.category.lower()==category.lower() for x in p.packages)]
    return result

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
    if not customer or customer.id!=payload.customer_id:raise HTTPException(403,"Customers can only create their own bookings")
    package=db.get(ServicePackage,payload.package_id)
    if not package:raise HTTPException(404,"Service package not found")
    try:booking=create_booking(db,payload.customer_id,package,payload.booking_date,payload.total)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    db.commit();db.refresh(booking);return booking
