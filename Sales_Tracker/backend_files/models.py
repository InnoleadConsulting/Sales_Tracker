# models.py
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend_files.db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    role = Column(String, nullable=False)
    
    # Relationships
    owned_opportunities = relationship("Opportunity", back_populates="owner")
    owned_activities = relationship("Activity", back_populates="owner")

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    industry = Column(String)
    country = Column(String)
    segment = Column(String)
    source = Column(String)
    notes = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    opportunities = relationship("Opportunity", back_populates="account")
    activities = relationship("Activity", back_populates="account")
    owner = relationship("User", foreign_keys=[owner_id])

class Opportunity(Base):
    __tablename__ = "opportunities"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    value_estimate = Column(Float)
    currency = Column(String, default="USD")
    stage = Column(String, nullable=False)
    probability = Column(Integer, default=0)
    expected_close_date = Column(Date)
    created_date = Column(Date)
    owner_id = Column(Integer, ForeignKey("users.id"))
    practice_area = Column(String)
    status = Column(String, default="Open")
    lost_reason = Column(Text)
    
    # Relationships
    account = relationship("Account", back_populates="opportunities")
    owner = relationship("User", back_populates="owned_opportunities")
    activities = relationship("Activity", back_populates="opportunity")

class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    activity_type = Column(String, nullable=False)
    activity_date = Column(Date, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    summary = Column(Text)
    next_step_date = Column(Date)
    next_step_action = Column(String)
    
    # Relationships
    account = relationship("Account", back_populates="activities")
    opportunity = relationship("Opportunity", back_populates="activities")
    owner = relationship("User", back_populates="owned_activities")