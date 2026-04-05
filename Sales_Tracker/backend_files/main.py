# main.py
from datetime import date, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend_files.db import SessionLocal, engine
from backend_files.models import Base, User, Account, Opportunity, Activity
import backend_files.schemas as schemas

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Innolead Sales Tracker API", version="1.0.0")

# Constants
STAGE_LEAD = "Lead"
STAGE_QUALIFIED = "Qualified"
STAGE_PROPOSAL = "Proposal"
STAGE_NEGOTIATION = "Negotiation"
STAGE_WON = "Won"
STAGE_LOST = "Lost"

ALLOWED_STAGES = {
    STAGE_LEAD, STAGE_QUALIFIED, STAGE_PROPOSAL, 
    STAGE_NEGOTIATION, STAGE_WON, STAGE_LOST
}

STATUS_OPEN = "Open"
STATUS_WON = "Won"
STATUS_LOST = "Lost"
ALLOWED_STATUSES = {STATUS_OPEN, STATUS_WON, STATUS_LOST}

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Validation functions
def validate_stage_value_probability(stage: str, value_estimate: Optional[float], probability: Optional[int]):
    if stage not in ALLOWED_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage '{stage}'")
    if probability is not None and not (0 <= probability <= 100):
        raise HTTPException(status_code=400, detail="Probability must be between 0 and 100")
    if stage in {STAGE_QUALIFIED, STAGE_PROPOSAL, STAGE_NEGOTIATION, STAGE_WON}:
        if value_estimate is None or value_estimate <= 0:
            raise HTTPException(status_code=400, detail="Value must be > 0 for this stage")

def validate_status_transition(new_status: Optional[str], new_stage: Optional[str], lost_reason: Optional[str]):
    if new_status is None:
        return
    if new_status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status '{new_status}'")
    if new_status == STATUS_LOST and (lost_reason is None or not lost_reason.strip()):
        raise HTTPException(status_code=400, detail="Lost reason required when marking as Lost")
    if new_status == STATUS_WON and new_stage is not None and new_stage != STAGE_WON:
        raise HTTPException(status_code=400, detail="Stage must be 'Won' when status is 'Won'")

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}

# ==================== USERS ====================
@app.post("/users", response_model=schemas.UserRead, status_code=201)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    user = User(
        name=user_in.name,
        email=user_in.email,
        role=user_in.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.get("/users", response_model=List[schemas.UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.name).all()

@app.get("/users/{user_id}", response_model=schemas.UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ==================== ACCOUNTS ====================
@app.post("/accounts", response_model=schemas.AccountRead, status_code=201)
def create_account(account_in: schemas.AccountCreate, db: Session = Depends(get_db)):
    account = Account(
        name=account_in.name,
        industry=account_in.industry,
        country=account_in.country,
        segment=account_in.segment,
        source=account_in.source,
        notes=account_in.notes
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account

@app.get("/accounts", response_model=List[schemas.AccountRead])
def list_accounts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Account).order_by(Account.name).offset(skip).limit(limit).all()

@app.get("/accounts/{account_id}", response_model=schemas.AccountRead)
def get_account(account_id: int, db: Session = Depends(get_db)):
    account = db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@app.patch("/accounts/{account_id}", response_model=schemas.AccountRead)
def update_account(account_id: int, account_in: schemas.AccountUpdate, db: Session = Depends(get_db)):
    account = db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    data = account_in.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(account, field, value)
    
    db.commit()
    db.refresh(account)
    return account

# ==================== OPPORTUNITIES ====================
@app.post("/opportunities", response_model=schemas.OpportunityRead, status_code=201)
def create_opportunity(opp_in: schemas.OpportunityCreate, db: Session = Depends(get_db)):
    account = db.get(Account, opp_in.account_id)
    if not account:
        raise HTTPException(status_code=400, detail="Account not found")

    stage = opp_in.stage or STAGE_LEAD
    status_value = opp_in.status or STATUS_OPEN

    validate_stage_value_probability(stage, opp_in.value_estimate, opp_in.probability)
    validate_status_transition(status_value, stage, opp_in.lost_reason)

    probability = opp_in.probability
    if status_value == STATUS_WON:
        probability = 100

    opp = Opportunity(
        account_id=opp_in.account_id,
        name=opp_in.name,
        description=opp_in.description,
        value_estimate=opp_in.value_estimate,
        currency=opp_in.currency,
        stage=stage,
        probability=probability,
        expected_close_date=opp_in.expected_close_date,
        created_date=opp_in.created_date or date.today(),
        owner_id=opp_in.owner_id,
        practice_area=opp_in.practice_area,
        status=status_value,
        lost_reason=opp_in.lost_reason
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)

    return schemas.OpportunityRead(
        id=opp.id,
        account_id=opp.account_id,
        name=opp.name,
        description=opp.description,
        value_estimate=opp.value_estimate,
        currency=opp.currency,
        stage=opp.stage,
        probability=opp.probability,
        expected_close_date=opp.expected_close_date,
        created_date=opp.created_date,
        owner_id=opp.owner_id,
        practice_area=opp.practice_area,
        status=opp.status,
        lost_reason=opp.lost_reason,
        account_name=account.name
    )

@app.get("/opportunities", response_model=List[schemas.OpportunityRead])
def list_opportunities(
    status_filter: Optional[str] = None,
    stage_filter: Optional[str] = None,
    owner_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    q = db.query(Opportunity, Account).join(Account)
    
    if status_filter:
        q = q.filter(Opportunity.status == status_filter)
    if stage_filter:
        q = q.filter(Opportunity.stage == stage_filter)
    if owner_id:
        q = q.filter(Opportunity.owner_id == owner_id)
    
    rows = q.order_by(Opportunity.expected_close_date).all()
    
    result = []
    for opp, acc in rows:
        result.append(schemas.OpportunityRead(
            id=opp.id,
            account_id=opp.account_id,
            name=opp.name,
            description=opp.description,
            value_estimate=opp.value_estimate,
            currency=opp.currency,
            stage=opp.stage,
            probability=opp.probability,
            expected_close_date=opp.expected_close_date,
            created_date=opp.created_date,
            owner_id=opp.owner_id,
            practice_area=opp.practice_area,
            status=opp.status,
            lost_reason=opp.lost_reason,
            account_name=acc.name
        ))
    return result

@app.get("/opportunities/{opportunity_id}", response_model=schemas.OpportunityRead)
def get_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    opp = db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    account = db.get(Account, opp.account_id)
    return schemas.OpportunityRead(
        id=opp.id,
        account_id=opp.account_id,
        name=opp.name,
        description=opp.description,
        value_estimate=opp.value_estimate,
        currency=opp.currency,
        stage=opp.stage,
        probability=opp.probability,
        expected_close_date=opp.expected_close_date,
        created_date=opp.created_date,
        owner_id=opp.owner_id,
        practice_area=opp.practice_area,
        status=opp.status,
        lost_reason=opp.lost_reason,
        account_name=account.name if account else None
    )

@app.patch("/opportunities/{opportunity_id}", response_model=schemas.OpportunityRead)
def update_opportunity(opportunity_id: int, opp_in: schemas.OpportunityUpdate, db: Session = Depends(get_db)):
    opp = db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    data = opp_in.dict(exclude_unset=True)
    
    # Handle stage/status transitions
    if 'status' in data and data['status'] == STATUS_WON:
        data['stage'] = STAGE_WON
        data['probability'] = 100
    elif 'status' in data and data['status'] == STATUS_LOST:
        data['stage'] = STAGE_LOST
    
    for field, value in data.items():
        setattr(opp, field, value)
    
    db.commit()
    db.refresh(opp)
    
    account = db.get(Account, opp.account_id)
    return schemas.OpportunityRead(
        id=opp.id,
        account_id=opp.account_id,
        name=opp.name,
        description=opp.description,
        value_estimate=opp.value_estimate,
        currency=opp.currency,
        stage=opp.stage,
        probability=opp.probability,
        expected_close_date=opp.expected_close_date,
        created_date=opp.created_date,
        owner_id=opp.owner_id,
        practice_area=opp.practice_area,
        status=opp.status,
        lost_reason=opp.lost_reason,
        account_name=account.name if account else None
    )

# ==================== ACTIVITIES ====================
@app.post("/activities", response_model=schemas.ActivityRead, status_code=201)
def create_activity(act_in: schemas.ActivityCreate, db: Session = Depends(get_db)):
    account = db.get(Account, act_in.account_id)
    if not account:
        raise HTTPException(status_code=400, detail="Account not found")

    activity_date = act_in.activity_date or date.today()

    act = Activity(
        account_id=act_in.account_id,
        opportunity_id=act_in.opportunity_id,
        activity_type=act_in.activity_type,
        activity_date=activity_date,
        owner_id=act_in.owner_id,
        summary=act_in.summary,
        next_step_date=act_in.next_step_date,
        next_step_action=act_in.next_step_action
    )
    db.add(act)
    db.commit()
    db.refresh(act)

    opp = db.get(Opportunity, act.opportunity_id) if act.opportunity_id else None
    owner = db.get(User, act.owner_id) if act.owner_id else None
    
    return schemas.ActivityRead(
        id=act.id,
        account_id=act.account_id,
        activity_type=act.activity_type,
        activity_date=act.activity_date,
        summary=act.summary,
        owner_id=act.owner_id,
        opportunity_id=act.opportunity_id,
        next_step_date=act.next_step_date,
        next_step_action=act.next_step_action,
        account_name=account.name,
        opportunity_name=opp.name if opp else None,
        owner_name=owner.name if owner else None
    )

@app.get("/activities", response_model=List[schemas.ActivityRead])
def list_activities(
    owner_id: Optional[int] = None,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    q = db.query(Activity, Account, Opportunity, User).join(
        Account, Activity.account_id == Account.id
    ).outerjoin(
        Opportunity, Activity.opportunity_id == Opportunity.id
    ).outerjoin(
        User, Activity.owner_id == User.id
    )
    
    if owner_id:
        q = q.filter(Activity.owner_id == owner_id)
    if account_id:
        q = q.filter(Activity.account_id == account_id)
    
    rows = q.order_by(Activity.activity_date.desc()).all()
    
    result = []
    for act, acc, opp, owner in rows:
        result.append(schemas.ActivityRead(
            id=act.id,
            account_id=act.account_id,
            activity_type=act.activity_type,
            activity_date=act.activity_date,
            summary=act.summary,
            owner_id=act.owner_id,
            opportunity_id=act.opportunity_id,
            next_step_date=act.next_step_date,
            next_step_action=act.next_step_action,
            account_name=acc.name,
            opportunity_name=opp.name if opp else None,
            owner_name=owner.name if owner else None
        ))
    return result