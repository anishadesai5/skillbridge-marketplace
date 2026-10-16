from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models import BookingStatus, MilestoneStatus, Role

class PackageOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int; provider_id:int; category:str; title:str; description:str; price:Decimal; duration_days:int

class ProviderOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int; first_name:str; last_name:str; bio:str|None; portfolio_url:str|None; rating:Decimal; packages:list[PackageOut]=[]

class ServiceListingOut(BaseModel):
    package_id:int
    provider_id:int
    provider_name:str
    provider_rating:Decimal
    category:str
    title:str
    description:str
    price:Decimal
    duration_days:int

class BookingCreate(BaseModel):
    package_id:int
    booking_date:date
    customer_notes:str|None=Field(default=None,max_length=2000)

class BookingOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int; customer_id:int; provider_id:int; package_id:int; status:str; booking_date:date; payment_held:bool; total:Decimal; customer_notes:str|None; created_at:datetime

class BookingTransitionRequest(BaseModel):
    status:BookingStatus

class MilestoneCreate(BaseModel):
    sequence:int=Field(gt=0)
    description:str=Field(min_length=3,max_length=4000)
    allocation_pct:Decimal=Field(gt=0,le=100,decimal_places=2)

class MilestoneBatchCreate(BaseModel):
    milestones:list[MilestoneCreate]=Field(min_length=1,max_length=20)

    @model_validator(mode="after")
    def validate_batch(self):
        sequences=[item.sequence for item in self.milestones]
        if len(sequences)!=len(set(sequences)):
            raise ValueError("Milestone sequences must be unique within a booking")
        total=sum((item.allocation_pct for item in self.milestones),Decimal("0"))
        if total!=Decimal("100"):
            raise ValueError("Milestone allocations must total 100 percent")
        return self

class MilestoneOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int
    booking_id:int
    sequence:int
    description:str
    status:MilestoneStatus
    allocation_pct:Decimal
    deliverable_url:str|None
    submitted_at:datetime|None
    approved_at:datetime|None

class BookingDetailOut(BookingOut):
    milestones:list[MilestoneOut]=[]

class HealthOut(BaseModel):
    status:str; database:str; payment_mode:str

class RegisterRequest(BaseModel):
    email:str=Field(min_length=5,max_length=255)
    password:str=Field(min_length=8,max_length=128)
    role:Role
    first_name:str=Field(min_length=1,max_length=100)
    last_name:str=Field(min_length=1,max_length=100)

class LoginRequest(BaseModel):
    email:str
    password:str

class UserOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int
    email:str
    role:Role
    is_active:bool

class TokenOut(BaseModel):
    access_token:str
    token_type:str="bearer"
    user:UserOut

class ProviderProfileUpdate(BaseModel):
    first_name:str=Field(min_length=1,max_length=100)
    last_name:str=Field(min_length=1,max_length=100)
    bio:str|None=Field(default=None,max_length=4000)
    portfolio_url:str|None=Field(default=None,max_length=500)

class CredentialCreate(BaseModel):
    credential_type:str=Field(min_length=2,max_length=100)
    document_url:str=Field(min_length=5,max_length=500)

class CredentialOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int
    provider_id:int
    credential_type:str
    document_url:str
    status:str

class ProviderAdminOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int
    first_name:str
    last_name:str
    status:str
    published:bool
    bio:str|None
    portfolio_url:str|None
    credentials:list[CredentialOut]=[]

class ProviderDecision(BaseModel):
    decision:str=Field(pattern="^(approve|reject)$")
    reason:str|None=Field(default=None,max_length=1000)
