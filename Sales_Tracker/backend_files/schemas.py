# schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime

# ==================== User Schemas ====================
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "Sales Rep"

class UserCreate(UserBase):
    pass

class UserRead(UserBase):
    id: int
    
    class Config:
        from_attributes = True

# ==================== Account Schemas ====================
class AccountBase(BaseModel):
    name: str
    industry: Optional[str] = None
    country: Optional[str] = None
    segment: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None

class AccountCreate(AccountBase):
    owner_id: Optional[int] = None

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    segment: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    owner_id: Optional[int] = None

class AccountRead(AccountBase):
    id: int
    owner_id: Optional[int] = None
    
    class Config:
        from_attributes = True

# ==================== Opportunity Schemas ====================
class OpportunityBase(BaseModel):
    account_id: int
    name: str
    description: Optional[str] = None
    value_estimate: Optional[float] = None
    currency: str = "USD"
    stage: str = "Lead"
    probability: Optional[int] = 0
    expected_close_date: Optional[date] = None
    created_date: Optional[date] = None
    owner_id: Optional[int] = None
    practice_area: Optional[str] = None
    status: str = "Open"
    lost_reason: Optional[str] = None

class OpportunityCreate(OpportunityBase):
    pass

class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    value_estimate: Optional[float] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    expected_close_date: Optional[date] = None
    owner_id: Optional[int] = None
    practice_area: Optional[str] = None
    status: Optional[str] = None
    lost_reason: Optional[str] = None

class OpportunityRead(OpportunityBase):
    id: int
    account_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# ==================== Activity Schemas ====================
class ActivityBase(BaseModel):
    account_id: int
    opportunity_id: Optional[int] = None
    activity_type: str
    activity_date: Optional[date] = None
    owner_id: Optional[int] = None
    summary: Optional[str] = None
    next_step_date: Optional[date] = None
    next_step_action: Optional[str] = None

class ActivityCreate(ActivityBase):
    pass

class ActivityRead(ActivityBase):
    id: int
    account_name: Optional[str] = None
    opportunity_name: Optional[str] = None
    owner_name: Optional[str] = None
    
    class Config:
        from_attributes = True