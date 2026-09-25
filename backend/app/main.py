from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload
from app.db import get_db
from app.models import Provider, ServicePackage
from app.schemas import BookingCreate, BookingOut, HealthOut, ProviderOut
from app.services import create_booking

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

@app.post("/bookings",response_model=BookingOut,status_code=201)
def bookings(payload:BookingCreate,db:Session=Depends(get_db)):
    package=db.get(ServicePackage,payload.package_id)
    if not package:raise HTTPException(404,"Service package not found")
    try:booking=create_booking(db,payload.customer_id,package,payload.booking_date,payload.total)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    db.commit();db.refresh(booking);return booking
