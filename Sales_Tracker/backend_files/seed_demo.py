# seed_demo.py
from datetime import date
from backend_files.db import Base, engine, SessionLocal
from backend_files.models import User, Account, Opportunity, Activity, ProductService, OpportunityProduct


def init_db():
    Base.metadata.create_all(bind=engine)


def seed():
    session = SessionLocal()

    # Create sample user
    og = User(name="OG", email="og@innolead.co.bw", role="Executive Director")
    session.add(og)
    session.flush()

    # Create sample account
    bac = Account(
        name="Botswana Accountancy College",
        industry="Education",
        country="Botswana",
        segment="Strategic",
        source="Existing client",
        owner_id=og.id,
        notes="Anchor client for AI and digital transformation."
    )
    session.add(bac)
    session.flush()

    # Sample product/service
    ai_service = ProductService(
        name="AI & Digital Transformation Partnership",
        description="Multi-year roadmap, EMIS/LMS, dashboards and change management.",
        category="Digital",
        typical_margin=0.35
    )
    session.add(ai_service)
    session.flush()

    # Opportunity
    opp = Opportunity(
        account_id=bac.id,
        name="BAC – AI & Digital Transformation Partnership",
        description="3-year programme to modernise digital capabilities.",
        value_estimate=1_200_000.0,
        currency="BWP",
        stage="Solution / Proposal",
        probability=50,
        expected_close_date=date(2026, 3, 31),
        created_date=date.today(),
        owner_id=og.id,
        practice_area="Digital",
        status="Open",
    )
    session.add(opp)
    session.flush()

    # Line item
    line = OpportunityProduct(
        opportunity_id=opp.id,
        product_id=ai_service.id,
        quantity=1,
        unit_price=1_200_000.0,
        total_price=1_200_000.0
    )
    session.add(line)

    # Activity
    act = Activity(
        account_id=bac.id,
        opportunity_id=opp.id,
        activity_type="Meeting",
        activity_date=date.today(),
        owner_id=og.id,
        summary="Presented concept and agreed to submit proposal.",
        next_step_date=date(2026, 1, 15),
        next_step_action="Submit detailed proposal and budget."
    )
    session.add(act)

    session.commit()
    session.close()


if __name__ == "__main__":
    init_db()
    seed()
    print("Database initialized and demo data seeded.")
