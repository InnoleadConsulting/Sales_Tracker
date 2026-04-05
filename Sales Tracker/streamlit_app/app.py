# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import requests
import base64
from pathlib import Path

# Page config FIRST
st.set_page_config(
    page_title="Innolead Sales Tracker",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to get base64 encoded image
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# API Configuration
API_BASE_URL = "http://localhost:8000"

# ==================== CACHED API FUNCTIONS(FASTER LOADING) ====================
@st.cache_data(ttl=60, show_spinner="Loading accounts...")
def get_cached_accounts():
    try:
        response = requests.get(f"{API_BASE_URL}/accounts", timeout=2)
        return response.json() if response.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=60, show_spinner="Loading opportunities...")
def get_cached_opportunities():
    try:
        response = requests.get(f"{API_BASE_URL}/opportunities", timeout=2)
        return response.json() if response.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=30, show_spinner="Loading activities...")
def get_cached_activities():
    try:
        response = requests.get(f"{API_BASE_URL}/activities", timeout=2)
        return response.json() if response.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=300, show_spinner="Loading users...")
def get_cached_users():
    try:
        response = requests.get(f"{API_BASE_URL}/users", timeout=2)
        return response.json() if response.status_code == 200 else []
    except:
        return []

# ==================== NON-CACHED WRITE OPERATIONS ====================
def create_account(data):
    try:
        response = requests.post(f"{API_BASE_URL}/accounts", json=data, timeout=5)
        if response.status_code in [200, 201]:
            st.cache_data.clear()
            return response.json()
    except:
        return None

def create_opportunity(data):
    try:
        response = requests.post(f"{API_BASE_URL}/opportunities", json=data, timeout=5)
        if response.status_code in [200, 201]:
            st.cache_data.clear()
            return response.json()
    except:
        return None

def create_activity(data):
    try:
        response = requests.post(f"{API_BASE_URL}/activities", json=data, timeout=5)
        if response.status_code in [200, 201]:
            st.cache_data.clear()
            return response.json()
    except:
        return None

def create_user(data):
    try:
        response = requests.post(f"{API_BASE_URL}/users", json=data, timeout=5)
        if response.status_code in [200, 201]:
            st.cache_data.clear()
            return response.json()
    except:
        return None

def update_opportunity(opp_id, data):
    try:
        response = requests.patch(f"{API_BASE_URL}/opportunities/{opp_id}", json=data, timeout=5)
        if response.status_code == 200:
            st.cache_data.clear()
            return response.json()
    except:
        return None

# ==================== HELPER FUNCTIONS ====================
def calculate_health_score(opp):
    """Calculate health score for an opportunity"""
    prob = opp.get('probability', 0)
    # Check recent activity
    has_recent_activity = False
    activities = get_cached_activities()
    for act in activities:
        if act.get('opportunity_id') == opp.get('id'):
            try:
                act_date = datetime.strptime(act.get('activity_date', '2000-01-01'), '%Y-%m-%d').date()
                if (date.today() - act_date).days < 14:
                    has_recent_activity = True
                    break
            except:
                continue
    
    if prob >= 70 and has_recent_activity:
        return 100, 'Healthy'
    elif prob >= 40 or has_recent_activity:
        return 60, 'At Risk'
    else:
        return 30, 'Critical'

def get_upcoming_follow_ups():
    """Get upcoming follow-ups from activities"""
    acts = get_cached_activities()
    today = date.today()
    follow_ups = []
    
    for act in acts:
        if act.get('next_step_date'):
            try:
                follow_date = datetime.strptime(act['next_step_date'], '%Y-%m-%d').date()
                days_diff = (follow_date - today).days
                
                if 0 <= days_diff <= 30:
                    follow_ups.append({
                        'date': follow_date,
                        'action': act.get('next_step_action', 'Follow-up'),
                        'account': act.get('account_name', 'Unknown'),
                        'opportunity': act.get('opportunity_name', 'N/A'),
                        'days': days_diff,
                        'type': 'urgent' if days_diff <= 3 else 'upcoming'
                    })
            except:
                continue
    
    return sorted(follow_ups, key=lambda x: x['days'])

# ==================== SIDEBAR ====================
with st.sidebar:
    # Try to load and display logo
    logo_path = (r"C:\Users\elvis\Desktop\innolead sales tracker\streamlit_app\assets\logo.png")  # Update this path to your logo location
    if Path(logo_path).exists():
        st.image(logo_path, use_container_width=True)
    else:
        # Fallback to text logo if image not found
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="color: black; font-size: 1.8rem; margin: 0;"> Innolead</h1>
            <p style="color: gray; margin: 0;">Sales Tracker</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["Dashboard", "Analytics", "Accounts", "Opportunities", "Activities", "Users"],
        key="navigation",
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Global Search
    search_query = st.text_input(" Search", placeholder="Search accounts, opportunities...", key="global_search")
    
    # Quick Stats
    with st.spinner("Loading..."):
        opps = get_cached_opportunities()
        acts = get_cached_activities()
    
    st.markdown("### Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Open Deals", len([o for o in opps if o.get('status') == 'Open']))
    with col2:
        st.metric("Activities", len(acts))
    
    st.markdown("---")
    st.caption("© 2026 Innolead")

# ==================== GLOBAL SEARCH RESULTS ====================
if search_query:
    st.title(f"Search Results for '{search_query}'")
    
    accounts = get_cached_accounts()
    opportunities = get_cached_opportunities()
    
    found_accounts = [a for a in accounts if search_query.lower() in a.get('name', '').lower()]
    found_opps = [o for o in opportunities if search_query.lower() in o.get('name', '').lower() 
                  or search_query.lower() in o.get('account_name', '').lower()]
    
    col1, col2 = st.columns(2)
    with col1:
        if found_accounts:
            st.subheader(f"Accounts ({len(found_accounts)})")
            for acc in found_accounts:
                st.write(f" {acc['name']}")
    
    with col2:
        if found_opps:
            st.subheader(f"Opportunities ({len(found_opps)})")
            for opp in found_opps:
                st.write(f" {opp['name']} - {opp.get('account_name', 'N/A')}")
    
    st.stop()

# ==================== DASHBOARD PAGE ====================
if page == "Dashboard":
    st.title("Dashboard Overview")
    
    # Load data
    with st.spinner("Loading dashboard..."):
        accounts = get_cached_accounts()
        opps = get_cached_opportunities()
        acts = get_cached_activities()
        follow_ups = get_upcoming_follow_ups()
    
    # Top Row - Main Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Accounts", len(accounts), help="Number of accounts in CRM")
    with col2:
        st.metric("Active Opportunities", len(opps), help="Total opportunities")
    with col3:
        st.metric("Activities", len(acts), help="Total logged activities")
    with col4:
        pipeline_value = sum(o.get('value_estimate', 0) for o in opps)
        st.metric("Pipeline Value", f"BWP{pipeline_value:,.0f}", help="Total value of all opportunities")
    
    st.markdown("---")
    
    # Health Dashboard Integration
    with st.expander(" Opportunity Health Dashboard", expanded=True):
        # Calculate health for each opportunity
        for opp in opps:
            score, status = calculate_health_score(opp)
            opp['health_score'] = score
            opp['health_status'] = status
        
        # Health filters
        col1, col2, col3 = st.columns(3)
        with col1:
            health_filter = st.selectbox("Filter by Health", ["All", "Healthy", "At Risk", "Critical"])
        with col2:
            min_value = st.number_input("Min Value (BWP)", min_value=0, value=0, step=10000)
        with col3:
            min_prob = st.slider("Min Probability (%)", 0, 100, 0)
        
        # Apply health filters
        filtered_opps = opps.copy()
        if health_filter != "All":
            filtered_opps = [o for o in filtered_opps if o.get('health_status') == health_filter]
        filtered_opps = [o for o in filtered_opps if o.get('value_estimate', 0) >= min_value]
        filtered_opps = [o for o in filtered_opps if o.get('probability', 0) >= min_prob]
        
        # Display health dashboard
        if filtered_opps:
            for opp in filtered_opps[:5]:
                health_color = {
                    'Healthy': '🟢',
                    'At Risk': '🟡',
                    'Critical': '🔴'
                }.get(opp.get('health_status'), '⚪')
                
                cols = st.columns([1, 3, 2, 2, 1])
                with cols[0]:
                    st.markdown(f"**{health_color}**")
                with cols[1]:
                    st.markdown(f"**{opp.get('name')}**")
                    st.caption(opp.get('account_name', 'N/A'))
                with cols[2]:
                    st.markdown(f"Score: **{opp.get('health_score')}**")
                    st.progress(opp.get('health_score', 0)/100)
                with cols[3]:
                    st.markdown(f"BWP{opp.get('value_estimate', 0):,.0f}")
                with cols[4]:
                    st.markdown(f"{opp.get('probability')}%")
                st.divider()
            
            if len(filtered_opps) > 5:
                st.caption(f"... and {len(filtered_opps) - 5} more opportunities")
        else:
            st.info("No opportunities match the filters")
    
    # Reminders Integration
    with st.expander(" Follow-up Reminders & Alerts", expanded=True):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            urgent_count = len([f for f in follow_ups if f['days'] <= 3])
            if urgent_count > 0:
                st.error(f"❗ {urgent_count} Urgent Follow-ups")
            else:
                st.success(" No urgent alerts")
            
            upcoming_7 = len([f for f in follow_ups if 0 <= f['days'] <= 7])
            upcoming_14 = len([f for f in follow_ups if 8 <= f['days'] <= 14])
            upcoming_30 = len([f for f in follow_ups if 15 <= f['days'] <= 30])
            
            st.metric("Next 7 Days", upcoming_7)
            st.metric("Next 7-14 Days", upcoming_14)
            st.metric("Next 14-30 Days", upcoming_30)
        
        with col2:
            if follow_ups:
                st.subheader("Upcoming Follow-ups")
                for f in follow_ups[:10]:
                    if f['days'] <= 3:
                        st.error(f"**{f['action']}** - Account: {f['account']} - Due: {f['date'].strftime('%A, %B %d')} ({f['days']} days)")
                    else:
                        st.warning(f"**{f['action']}** - Account: {f['account']} - Due: {f['date'].strftime('%A, %B %d')} ({f['days']} days)")
            else:
                st.info("No upcoming follow-ups")
    
    st.markdown("---")
    
    # Pipeline Snapshot
    st.subheader("Pipeline Snapshot")
    
    if opps:
        df = pd.DataFrame(opps)
        display_cols = ['name', 'account_name', 'stage', 'status', 'value_estimate', 'probability', 'expected_close_date']
        available_cols = [c for c in display_cols if c in df.columns]
        
        if available_cols:
            display_df = df[available_cols].copy()
            display_df.columns = ['Opportunity', 'Account', 'Stage', 'Status', 'Value', 'Prob %', 'Close Date']
            st.dataframe(display_df, use_container_width=True, height=300)
    else:
        st.info("No opportunities yet")

# ==================== ANALYTICS PAGE ====================
elif page == "Analytics":
    st.title("Analytics")
    
    with st.spinner("Loading analytics..."):
        opps = get_cached_opportunities()
        
        # Add health scores for analytics
        for opp in opps:
            score, status = calculate_health_score(opp)
            opp['health_score'] = score
            opp['health_status'] = status
    
    if opps:
        # KPI calculations
        pipeline_value = sum(o.get('value_estimate', 0) for o in opps)
        weighted_forecast = sum(o.get('value_estimate', 0) * o.get('probability', 0) / 100 for o in opps)
        won_value = sum(o.get('value_estimate', 0) for o in opps if o.get('status') == 'Won')
        won_count = len([o for o in opps if o.get('status') == 'Won'])
        total_closed = len([o for o in opps if o.get('status') in ['Won', 'Lost']])
        win_rate = (won_count / total_closed * 100) if total_closed > 0 else 0
        avg_deal = pipeline_value / len(opps) if opps else 0
        
        # KPI Row
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Pipeline Value", f"BWP{pipeline_value:,.0f}")
        with col2:
            st.metric("Weighted Forecast", f"BWP{weighted_forecast:,.0f}")
        with col3:
            st.metric("Won Value", f"BWP{won_value:,.0f}")
        with col4:
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col5:
            st.metric("Avg Deal Size", f"BWP{avg_deal:,.0f}")
        
        st.markdown("---")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Pipeline Value by Stage")
            stage_data = {}
            for opp in opps:
                stage = opp.get('stage', 'Unknown')
                value = opp.get('value_estimate', 0)
                stage_data[stage] = stage_data.get(stage, 0) + value
            
            if stage_data:
                df_stage = pd.DataFrame(list(stage_data.items()), columns=['Stage', 'Value'])
                fig = px.bar(df_stage, x='Stage', y='Value', title='Pipeline by Stage')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Opportunity Health Distribution")
            health_counts = {
                'Healthy': len([o for o in opps if o.get('health_status') == 'Healthy']),
                'At Risk': len([o for o in opps if o.get('health_status') == 'At Risk']),
                'Critical': len([o for o in opps if o.get('health_status') == 'Critical'])
            }
            
            if sum(health_counts.values()) > 0:
                df_health = pd.DataFrame(list(health_counts.items()), columns=['Status', 'Count'])
                fig = px.pie(df_health, values='Count', names='Status', title='Opportunity Health')
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for analytics")

# ==================== ACCOUNTS PAGE ====================
elif page == "Accounts":
    st.title("Accounts")
    
    tab1, tab2 = st.tabs([" List View", " Add New Account"])
    
    with tab1:
        with st.spinner("Loading accounts..."):
            accounts = get_cached_accounts()
        
        if accounts:
            df = pd.DataFrame(accounts)
            display_cols = ['name', 'industry', 'segment', 'country', 'notes']
            available_cols = [c for c in display_cols if c in df.columns]
            
            if available_cols:
                display_df = df[available_cols].copy()
                display_df.columns = ['Account Name', 'Industry', 'Segment', 'Country', 'Notes']
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No accounts found")
    
    with tab2:
        with st.form("new_account"):
            st.subheader("Create New Account")
            
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Account Name *")
                industry = st.text_input("Industry")
                country = st.text_input("Country", value="Botswana")
            with col2:
                segment = st.selectbox("Segment", ["Enterprise", "SME", "Government", "Startup"])
                source = st.selectbox("Lead Source", ["Website", "Referral", "Conference", "Cold Call"])
            
            notes = st.text_area("Notes")
            
            submitted = st.form_submit_button(" Create Account", use_container_width=True)
            if submitted and name:
                data = {
                    "name": name,
                    "industry": industry,
                    "country": country,
                    "segment": segment,
                    "source": source,
                    "notes": notes
                }
                result = create_account(data)
                if result:
                    st.success(f" Account '{name}' created!")
                    st.balloons()
                    st.rerun()

# ==================== OPPORTUNITIES PAGE ====================
elif page == "Opportunities":
    st.title("Opportunities")
    
    tab1, tab2, tab3 = st.tabs([" Pipeline Overview", " New Opportunity", " Edit Owner"])
    
    with tab1:
        with st.spinner("Loading opportunities..."):
            opps = get_cached_opportunities()
            
            # Add health scores
            for opp in opps:
                score, status = calculate_health_score(opp)
                opp['health_score'] = score
                opp['health_status'] = status
        
        # Pipeline stats
        total = len(opps)
        open_opps = len([o for o in opps if o.get('status') == 'Open'])
        won = len([o for o in opps if o.get('status') == 'Won'])
        lost = len([o for o in opps if o.get('status') == 'Lost'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", total)
        with col2:
            st.metric("Open", open_opps)
        with col3:
            st.metric("Won", won)
        with col4:
            st.metric("Lost", lost)
        
        # Opportunities list with health
        if opps:
            st.subheader("Opportunities List")
            df = pd.DataFrame(opps)
            display_df = df[['id', 'account_name', 'name', 'stage', 'value_estimate', 
                           'probability', 'status', 'health_status']].copy()
            display_df.columns = ['ID', 'Account', 'Opportunity', 'Stage', 'Value', 
                                'Prob %', 'Status', 'Health']
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    with tab2:
        accounts = get_cached_accounts()
        users = get_cached_users()
        
        if accounts and users:
            with st.form("new_opportunity"):
                st.subheader("Create New Opportunity")
                
                col1, col2 = st.columns(2)
                with col1:
                    account = st.selectbox("Account *", [a['name'] for a in accounts])
                    name = st.text_input("Opportunity Name *")
                    stage = st.selectbox("Stage", ["Lead", "Qualified", "Proposal", "Negotiation"])
                
                with col2:
                    owner = st.selectbox("Owner *", [u['name'] for u in users])
                    value = st.number_input("Value (BWP)", min_value=0.0, value=50000.0, step=1000.0)
                    probability = st.slider("Probability (%)", 0, 100, 50)
                
                close_date = st.date_input("Expected Close Date", value=date.today() + timedelta(days=30))
                
                submitted = st.form_submit_button(" Create Opportunity", use_container_width=True)
                if submitted and name and account:
                    account_id = next(a['id'] for a in accounts if a['name'] == account)
                    owner_id = next(u['id'] for u in users if u['name'] == owner)
                    
                    data = {
                        "account_id": account_id,
                        "name": name,
                        "value_estimate": value,
                        "stage": stage,
                        "probability": probability,
                        "owner_id": owner_id,
                        "expected_close_date": close_date.isoformat(),
                        "status": "Open"
                    }
                    result = create_opportunity(data)
                    if result:
                        st.success(f" Opportunity '{name}' created!")
                        st.balloons()
                        st.rerun()
        else:
            st.warning("Please create accounts and users first")
    
    with tab3:
        opps = get_cached_opportunities()
        users = get_cached_users()
        
        if opps and users:
            st.subheader("Edit Opportunity Owner")
            
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                selected_opp = st.selectbox("Select Opportunity", [o['name'] for o in opps])
            with col2:
                new_owner = st.selectbox("New Owner", [u['name'] for u in users])
            with col3:
                if st.button("Update Owner", use_container_width=True):
                    opp_id = next(o['id'] for o in opps if o['name'] == selected_opp)
                    owner_id = next(u['id'] for u in users if u['name'] == new_owner)
                    
                    result = update_opportunity(opp_id, {"owner_id": owner_id})
                    if result:
                        st.success(f" Owner updated to {new_owner}")
                        st.rerun()

# ==================== ACTIVITIES PAGE ====================
elif page == "Activities":
    st.title("Activities Log")
    
    tab1, tab2 = st.tabs([" All Activities", " Follow-up Reminders"])
    
    with tab1:
        with st.spinner("Loading data..."):
            acts = get_cached_activities()
            users = get_cached_users()
            accounts = get_cached_accounts()
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            type_filter = st.selectbox("Filter by Type", ["All", "Call", "Meeting", "Email", "Proposal"])
        with col2:
            user_names = ["All"] + [u['name'] for u in users]
            owner_filter = st.selectbox("Filter by Owner", user_names)
        with col3:
            account_names = ["All"] + [a['name'] for a in accounts]
            account_filter = st.selectbox("Filter by Account", account_names)
        
        # Apply filters
        filtered_acts = acts.copy()
        if type_filter != "All":
            filtered_acts = [a for a in filtered_acts if a.get('activity_type') == type_filter]
        if owner_filter != "All":
            filtered_acts = [a for a in filtered_acts if a.get('owner_name') == owner_filter]
        if account_filter != "All":
            filtered_acts = [a for a in filtered_acts if a.get('account_name') == account_filter]
        
        st.caption(f"Showing {len(filtered_acts)} of {len(acts)} activities")
        
        # Display activities
        if filtered_acts:
            df = pd.DataFrame(filtered_acts)
            display_cols = ['activity_date', 'activity_type', 'account_name', 'owner_name', 'summary', 'next_step_date']
            available_cols = [c for c in display_cols if c in df.columns]
            
            if available_cols:
                display_df = df[available_cols].copy()
                display_df.columns = ['Date', 'Type', 'Account', 'Owner', 'Summary', 'Next Step']
                st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    with tab2:
        st.subheader("Follow-up Reminders")
        
        follow_ups = get_upcoming_follow_ups()
        
        if follow_ups:
            urgent = [f for f in follow_ups if f['days'] <= 3]
            upcoming = [f for f in follow_ups if f['days'] > 3]
            
            if urgent:
                st.error("❗ Urgent (Next 3 Days)")
                for f in urgent:
                    st.write(f"**{f['action']}** - Account: {f['account']} - Opportunity: {f['opportunity']} - Due: {f['date'].strftime('%A, %B %d')} ({f['days']} days)")
            
            if upcoming:
                st.warning(" Upcoming")
                for f in upcoming[:10]:
                    st.write(f"**{f['action']}** - Account: {f['account']} - Due: {f['date'].strftime('%A, %B %d')} ({f['days']} days)")
        else:
            st.info("No upcoming follow-ups")
    
    # Log New Activity
    with st.expander(" Log New Activity", expanded=False):
        if accounts and users:
            with st.form("new_activity"):
                col1, col2 = st.columns(2)
                with col1:
                    account = st.selectbox("Account *", [a['name'] for a in accounts])
                    activity_type = st.selectbox("Activity Type *", ["Call", "Meeting", "Email", "Proposal"])
                    activity_date = st.date_input("Activity Date", value=date.today())
                
                with col2:
                    opps = get_cached_opportunities()
                    opportunity = st.selectbox("Opportunity", ["-- None --"] + [o['name'] for o in opps])
                    owner = st.selectbox("Owner *", [u['name'] for u in users])
                
                summary = st.text_area("Summary / Notes")
                
                col3, col4 = st.columns(2)
                with col3:
                    next_step_date = st.date_input("Next Step Date", value=None)
                with col4:
                    next_step_action = st.text_input("Next Step Action")
                
                submitted = st.form_submit_button(" Log Activity", use_container_width=True)
                if submitted and account and activity_type:
                    account_id = next(a['id'] for a in accounts if a['name'] == account)
                    owner_id = next(u['id'] for u in users if u['name'] == owner)
                    opp_id = None
                    if opportunity != "-- None --":
                        opp_id = next(o['id'] for o in opps if o['name'] == opportunity)
                    
                    data = {
                        "account_id": account_id,
                        "activity_type": activity_type,
                        "activity_date": activity_date.isoformat(),
                        "owner_id": owner_id,
                        "summary": summary,
                        "opportunity_id": opp_id,
                        "next_step_date": next_step_date.isoformat() if next_step_date else None,
                        "next_step_action": next_step_action
                    }
                    result = create_activity(data)
                    if result:
                        st.success(" Activity logged!")
                        st.rerun()
        else:
            st.warning("Please create accounts and users first")

# ==================== USERS PAGE ====================
elif page == "Users":
    st.title("Users")
    
    with st.spinner("Loading users..."):
        users = get_cached_users()
    
    # User List Section
    st.subheader("User List")
    
    if users:
        df = pd.DataFrame(users)
        display_cols = ['name', 'email', 'role', 'id']
        available_cols = [c for c in display_cols if c in df.columns]
        
        if available_cols:
            display_df = df[available_cols].copy()
            display_df.columns = ['Name', 'Email', 'Role', 'ID']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No users yet")
    
    st.markdown("---")
    
    # Search Section (matching screenshot)
    st.subheader("Search")
    search_input = st.text_input("", placeholder="Search accounts, opportunities...", label_visibility="collapsed")
    
    st.markdown("---")
    
    # User Statistics Section
    st.subheader("Users by Role:")
    
    if users:
        # Calculate role counts
        roles = {}
        for user in users:
            role = user.get('role', 'Unspecified')
            roles[role] = roles.get(role, 0) + 1
        
        # Display in a nice format
        for role, count in roles.items():
            st.markdown(f"- {role}: {count}")
        
        # Also show total users
        st.markdown(f"\n**Total Users**: {len(users)}")
    else:
        st.markdown("- No users found")
        st.markdown("\n**Total Users**: 0")
    
    st.markdown("---")
    
    # Add New User Section
    with st.expander(" Add New User", expanded=False):
        with st.form("new_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name *")
                email = st.text_input("Email *")
            with col2:
                role = st.selectbox("Role", ["Consultant", "Manager", "Director", "Admin"])
            
            submitted = st.form_submit_button(" Create User", use_container_width=True)
            
            if submitted:
                if not name or not email:
                    st.error("Name and Email are required")
                elif "@" not in email:
                    st.error("Please enter a valid email address")
                else:
                    data = {
                        "name": name,
                        "email": email,
                        "role": role
                    }
                    result = create_user(data)
                    if result:
                        st.success(f"User '{name}' created successfully!")
                        st.balloons()
                        st.rerun()