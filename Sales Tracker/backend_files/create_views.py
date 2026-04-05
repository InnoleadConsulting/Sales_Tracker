# create_views.py
from db import engine

VIEW_SQL = """
CREATE VIEW IF NOT EXISTS v_opportunities AS
SELECT
    o.id,
    o.name,
    o.description,
    o.value_estimate,
    o.currency,
    o.stage,
    o.probability,
    o.expected_close_date,
    o.created_date,
    o.practice_area,
    o.status,
    o.lost_reason,
    a.id AS account_id,
    a.name AS account_name,
    a.industry AS account_industry,
    a.segment AS account_segment,
    a.country AS account_country,
    u.id AS owner_id,
    u.name AS owner_name,
    u.role AS owner_role
FROM opportunities o
JOIN accounts a ON o.account_id = a.id
LEFT JOIN users u ON o.owner_id = u.id;

CREATE VIEW IF NOT EXISTS v_activities AS
SELECT
    act.id,
    act.activity_type,
    act.activity_date,
    act.summary,
    act.next_step_date,
    act.next_step_action,
    a.id AS account_id,
    a.name AS account_name,
    o.id AS opportunity_id,
    o.name AS opportunity_name,
    u.id AS owner_id,
    u.name AS owner_name
FROM activities act
JOIN accounts a ON act.account_id = a.id
LEFT JOIN opportunities o ON act.opportunity_id = o.id
LEFT JOIN users u ON act.owner_id = u.id;
"""

if __name__ == "__main__":
    with engine.connect() as conn:
        for stmt in VIEW_SQL.strip().split(";"):
            if stmt.strip():
                conn.exec_driver_sql(stmt)
    print("Views created: v_opportunities, v_activities")
