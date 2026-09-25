from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

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
