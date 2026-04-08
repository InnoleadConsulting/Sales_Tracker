# utils.py
import pandas as pd

def df_from_list_of_dicts(data):
    """Convert list of dicts to pandas DataFrame"""
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

def format_currency(value):
    """Format currency values"""
    if value is None:
        return "$0"
    return f"${value:,.0f}"

def calculate_health_score(opportunity):
    """Calculate health score for an opportunity"""
    score = 0
    if opportunity.get('probability'):
        score += opportunity['probability'] * 0.7
    
    # Add points for recent activity
    if opportunity.get('last_activity_date'):
        days_since = (pd.Timestamp.now() - pd.Timestamp(opportunity['last_activity_date'])).days
        if days_since < 7:
            score += 30
        elif days_since < 14:
            score += 15
    
    return min(100, score)