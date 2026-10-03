from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.models import Role

class PackageOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int; provider_id:int; category:str; title:str; description:str; price:Decimal; duration_days:int

class ProviderOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int; first_name:str; last_name:str; bio:str|None; portfolio_url:str|None; rating:Decimal; packages:list[PackageOut]=[]

class BookingCreate(BaseModel):
    customer_id:int; package_id:int; booking_date:date; total:Decimal=Field(gt=0)

class BookingOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int; customer_id:int; provider_id:int; package_id:int; status:str; booking_date:date; payment_held:bool; total:Decimal

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
