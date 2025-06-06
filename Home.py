import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import re
import json
import os
import hashlib
# pyright: ignore[reportMissingImports

# Supabase config
SUPABASE_URL = "https://pjhgxmxjsncqnzxeqdjt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqaGd4bXhqc25jcW56eGVxZGp0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxODgxMTUsImV4cCI6MjA2NDc2NDExNX0.H-UY1jbbutuUFUeSMrozPdEzqA4UTT_b7HWeF4Ljo3Q"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# File paths for team management data
USERS_FILE = "users_roles.json"
TEAMS_FILE = "teams.json"
TECH_LEADS_FILE = "tech_leads.json"

# Initialize session state
def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0
    if 'last_attempt' not in st.session_state:
        st.session_state.last_attempt = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = ""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"
    if 'tech_lead_verified' not in st.session_state:
        st.session_state.tech_lead_verified = False

# Team management helper functions
def load_data(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def hash_token(token):
    """Hash the personal access token for security"""
    return hashlib.sha256(token.encode()).hexdigest()

def verify_personal_access_token(token):
    """Verify if the token meets security requirements"""
    if len(token) < 20:
        return False, "Token must be at least 20 characters long"
    if not re.search(r"[A-Za-z]", token):
        return False, "Token must contain letters"
    if not re.search(r"[0-9]", token):
        return False, "Token must contain numbers"
    return True, "Valid token"

def get_user_role():
    users = load_data(USERS_FILE)
    return users.get(st.session_state.username, {}).get('role', '')

def set_user_role(role):
    users = load_data(USERS_FILE)
    if st.session_state.username not in users:
        users[st.session_state.username] = {}
    users[st.session_state.username]['role'] = role
    users[st.session_state.username]['registered_at'] = datetime.now().isoformat()
    save_data(users, USERS_FILE)
    st.session_state.user_role = role

def register_tech_lead(token):
    """Register tech lead with personal access token"""
    tech_leads = load_data(TECH_LEADS_FILE)
    tech_leads[st.session_state.username] = {
        'token_hash': hash_token(token),
        'registered_at': datetime.now().isoformat(),
        'status': 'active'
    }
    save_data(tech_leads, TECH_LEADS_FILE)
    st.session_state.tech_lead_verified = True

def is_tech_lead_verified():
    """Check if current user is a verified tech lead"""
    tech_leads = load_data(TECH_LEADS_FILE)
    return st.session_state.username in tech_leads

def get_all_teams():
    """Get all teams created by developer interns"""
    teams = load_data(TEAMS_FILE)
    users = load_data(USERS_FILE)
    
    all_teams = []
    for team_key, team_data in teams.items():
        leader = team_data.get('leader', '')
        if leader in users and users[leader].get('role') == 'Developer Intern':
            team_info = {
                'team_id': team_key,
                'leader': leader,
                'members': team_data.get('members', []),
                'created_at': team_data.get('created_at', ''),
                'member_count': len(team_data.get('members', []))
            }
            all_teams.append(team_info)
    
    return all_teams

def get_platform_stats():
    """Get overall platform statistics"""
    users = load_data(USERS_FILE)
    teams = load_data(TEAMS_FILE)
    tech_leads = load_data(TECH_LEADS_FILE)
    
    stats = {
        'total_users': len(users),
        'tech_leads': len(tech_leads),
        'developer_interns': len([u for u in users.values() if u.get('role') == 'Developer Intern']),
        'total_teams': len(teams),
        'total_team_members': sum(len(team.get('members', [])) for team in teams.values())
    }
    return stats

# Original authentication functions
def is_valid_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Must include an uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Must include a lowercase letter"
    if not re.search(r"\d", password):
        return False, "Must include a digit"
    return True, "Valid"

def register_user(email, password):
    try:
        supabase.auth.sign_up({"email": email, "password": password})
        return True, "Registered successfully. Please check your email to verify your account."
    except Exception as e:
        return False, str(e)

def login_user(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            return True, email
        else:
            return False, "Login failed. Please make sure your email is verified."
    except Exception as e:
        return False, str(e)

def check_rate_limit():
    if st.session_state.login_attempts >= 3:
        if st.session_state.last_attempt:
            time_diff = datetime.now() - st.session_state.last_attempt
            if time_diff < timedelta(minutes=5):
                return False, f"Too many failed attempts. Try again in {5 - time_diff.seconds // 60} minutes."
        else:
            st.session_state.login_attempts = 0
    return True, ""

def login_page():
    st.title("🔐 Supabase Auth Login")

    can_attempt, rate_limit_msg = check_rate_limit()
    if not can_attempt:
        st.error(rate_limit_msg)
        return

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            email = st.text_input("Email").strip()
            password = st.text_input("Password", type="password").strip()
            submit = st.form_submit_button("Login")

            if submit:
                if email and password:
                    valid, msg = login_user(email, password)
                    if valid:
                        st.session_state.logged_in = True
                        st.session_state.username = msg
                        st.session_state.login_attempts = 0
                        st.session_state.user_role = get_user_role()
                        st.session_state.tech_lead_verified = is_tech_lead_verified()
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.session_state.login_attempts += 1
                        st.session_state.last_attempt = datetime.now()
                        st.error(f"❌ {msg} (Attempt {st.session_state.login_attempts}/3)")
                        if "confirmation" in msg.lower() or "verify" in msg.lower():
                            st.info("Please check your inbox and verify your email before logging in.")
                else:
                    st.error("Please enter both email and password.")

    with tab2:
        st.subheader("Register")
        with st.form("register_form"):
            email = st.text_input("Email").strip()
            password = st.text_input("Password", type="password").strip()
            confirm_password = st.text_input("Confirm Password", type="password").strip()
            submit = st.form_submit_button("Register")

            if submit:
                if password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    valid, msg = is_valid_password(password)
                    if not valid:
                        st.error(msg)
                    else:
                        success, msg = register_user(email, password)
                        if success:
                            st.success(msg)
                        else:
                            st.error(f"Registration failed: {msg}")

def tech_lead_registration():
    """Tech Lead registration with personal access token"""
    st.subheader("🔐 Tech Lead Registration")
    st.info("As a Tech Lead, you need to provide a Personal Access Token for enhanced security.")
    
    with st.form("tech_lead_form"):
        st.write("**Security Requirements:**")
        st.write("• Token must be at least 20 characters")
        st.write("• Must contain both letters and numbers")
        st.write("• Keep your token secure - it will be encrypted")
        
        token = st.text_input("Personal Access Token", type="password", 
                             placeholder="Enter your GitLab/GitHub Personal Access Token")
        
        confirm_token = st.text_input("Confirm Token", type="password",
                                     placeholder="Re-enter your token")
        
        agree = st.checkbox("I understand that this token will be used for team management and security purposes")
        
        submit = st.form_submit_button("Register as Tech Lead")
        
        if submit:
            if not agree:
                st.error("Please agree to the terms to proceed.")
            elif token != confirm_token:
                st.error("Tokens do not match.")
            else:
                valid, msg = verify_personal_access_token(token)
                if valid:
                    register_tech_lead(token)
                    set_user_role('Tech Lead')
                    st.success("✅ Successfully registered as Tech Lead!")
                    st.success("🔒 Your token has been securely encrypted and stored.")
                    st.rerun()
                else:
                    st.error(f"Invalid token: {msg}")

def user_dashboard():
    st.header("📊 User Dashboard")
    st.success(f"Welcome, {st.session_state.username}")
    
    # Display current role if set
    if st.session_state.user_role:
        role_emoji = "👨‍💼" if st.session_state.user_role == "Tech Lead" else "👨‍💻"
        st.info(f"{role_emoji} Current Role: {st.session_state.user_role}")
        
        if st.session_state.user_role == "Tech Lead" and st.session_state.tech_lead_verified:
            st.success("🔒 Verified Tech Lead Account")
    
    # Role registration section (only if no role assigned)
    if not st.session_state.user_role:
        st.subheader("🎯 Choose Your Role")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("👨‍💼 Register as Tech Lead", use_container_width=True):
                st.session_state.current_page = "tech_lead_registration"
                st.rerun()
        
        with col2:
            if st.button("👨‍💻 Register as Developer Intern", use_container_width=True):
                set_user_role('Developer Intern')
                st.success("✅ Registered as Developer Intern!")
                st.rerun()
    
    # Role-specific options
    if st.session_state.user_role == 'Developer Intern':
        st.divider()
        st.subheader("👥 Team Management")
        if st.button("Manage Your Team", use_container_width=True):
            st.session_state.current_page = "team_management"
            st.rerun()
    
    elif st.session_state.user_role == 'Tech Lead' and st.session_state.tech_lead_verified:
        st.divider()
        st.subheader("🎛️ Tech Lead Controls")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 View All Teams", use_container_width=True):
                st.session_state.current_page = "manage_all_teams"
                st.rerun()
        
        with col2:
            if st.button("📊 Platform Analytics", use_container_width=True):
                st.session_state.current_page = "platform_analytics"
                st.rerun()
    
    # Original dashboard content
    if st.session_state.user_role:
        st.divider()
        st.subheader("📈 Your Activity")
        st.metric("Activity Score", "89%", "5%")
        st.line_chart({"Progress": [10, 25, 35, 70, 90]})

def team_management_page():
    st.title("👥 Team Management")
    st.write(f"Team Leader: {st.session_state.username}")
    
    # Load existing teams
    teams = load_data(TEAMS_FILE)
    user_team_key = f"{st.session_state.username}_team"
    
    if user_team_key not in teams:
        teams[user_team_key] = {
            'leader': st.session_state.username,
            'members': [],
            'created_at': datetime.now().isoformat()
        }
        save_data(teams, TEAMS_FILE)
    
    current_team = teams[user_team_key]
    
    # Display current team members
    st.subheader("Current Team Members")
    if current_team['members']:
        for i, member in enumerate(current_team['members'], 1):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{i}. **{member['name']}** (GitLab: @{member['gitlab_username']})")
            with col2:
                if st.button(f"Remove", key=f"remove_{i}"):
                    current_team['members'].pop(i-1)
                    teams[user_team_key] = current_team
                    save_data(teams, TEAMS_FILE)
                    st.success(f"Removed {member['name']} from team!")
                    st.rerun()
    else:
        st.info("No team members added yet.")
    
    # Add new team member
    st.subheader("Add Team Member")
    
    if len(current_team['members']) >= 5:
        st.warning("⚠️ Maximum team size reached (5 members)")
    else:
        with st.form("add_member_form"):
            st.write(f"Remaining slots: {5 - len(current_team['members'])}")
            
            member_name = st.text_input("Friend's Name", placeholder="Enter your friend's name")
            gitlab_username = st.text_input("GitLab Username", placeholder="Enter GitLab username (without @)")
            
            submit = st.form_submit_button("Add Team Member")
            
            if submit:
                if member_name and gitlab_username:
                    # Check if GitLab username already exists in team
                    existing_usernames = [member['gitlab_username'].lower() for member in current_team['members']]
                    if gitlab_username.lower() in existing_usernames:
                        st.error("This GitLab username is already in your team!")
                    else:
                        new_member = {
                            'name': member_name,
                            'gitlab_username': gitlab_username,
                            'added_at': datetime.now().isoformat()
                        }
                        current_team['members'].append(new_member)
                        teams[user_team_key] = current_team
                        save_data(teams, TEAMS_FILE)
                        st.success(f"Added {member_name} to your team!")
                        st.rerun()
                else:
                    st.error("Please fill in both name and GitLab username.")
    
    # Team statistics
    st.divider()
    st.subheader("📊 Team Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Team Size", len(current_team['members']))
    with col2:
        st.metric("Available Slots", 5 - len(current_team['members']))
    with col3:
        created_date = datetime.fromisoformat(current_team['created_at']).strftime("%Y-%m-%d")
        st.metric("Created", created_date)

def manage_all_teams_page():
    st.title("🎛️ Tech Lead - Team Management")
    st.subheader("All Developer Intern Teams")
    
    all_teams = get_all_teams()
    
    if not all_teams:
        st.info("No teams have been created yet by Developer Interns.")
        return
    
    # Search and filter options
    search_term = st.text_input("🔍 Search teams by leader name", placeholder="Type leader name...")
    
    # Filter teams based on search
    filtered_teams = all_teams
    if search_term:
        filtered_teams = [team for team in all_teams if search_term.lower() in team['leader'].lower()]
    
    # Display teams
    for i, team in enumerate(filtered_teams, 1):
        with st.expander(f"Team {i}: {team['leader']} ({team['member_count']} members)", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Team Leader:** {team['leader']}")
                st.write(f"**Created:** {datetime.fromisoformat(team['created_at']).strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Team Members:** {team['member_count']}/5")
                
                if team['members']:
                    st.write("**Members:**")
                    for j, member in enumerate(team['members'], 1):
                        st.write(f"  {j}. {member['name']} (@{member['gitlab_username']})")
                else:
                    st.write("*No members added yet*")
            
            with col2:
                # Team actions
                if st.button(f"📧 Contact Leader", key=f"contact_{i}"):
                    st.info(f"Contact: {team['leader']}")
                
                if st.button(f"📊 Team Details", key=f"details_{i}"):
                    st.json(team)
                
                # Emergency controls
                if st.button(f"⚠️ Freeze Team", key=f"freeze_{i}"):
                    st.warning("Team freeze functionality - implement as needed")
    
    # Summary statistics
    st.divider()
    st.subheader("📈 Teams Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Teams", len(all_teams))
    with col2:
        active_teams = len([t for t in all_teams if t['member_count'] > 0])
        st.metric("Active Teams", active_teams)
    with col3:
        avg_size = sum(t['member_count'] for t in all_teams) / len(all_teams) if all_teams else 0
        st.metric("Avg Team Size", f"{avg_size:.1f}")
    with col4:
        full_teams = len([t for t in all_teams if t['member_count'] == 5])
        st.metric("Full Teams", full_teams)

def platform_analytics_page():
    st.title("📊 Platform Analytics")
    st.subheader("Tech Lead Dashboard")
    
    stats = get_platform_stats()
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", stats['total_users'])
    with col2:
        st.metric("Tech Leads", stats['tech_leads'])
    with col3:
        st.metric("Developer Interns", stats['developer_interns'])
    with col4:
        st.metric("Total Teams", stats['total_teams'])
    
    st.divider()
    
    # Detailed analytics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 User Distribution")
        user_data = {
            'Role': ['Tech Lead', 'Developer Intern', 'Unassigned'],
            'Count': [stats['tech_leads'], stats['developer_interns'], 
                     stats['total_users'] - stats['tech_leads'] - stats['developer_interns']]
        }
        st.bar_chart(data=user_data, x='Role', y='Count')
    
    with col2:
        st.subheader("👥 Team Statistics")
        st.metric("Total Team Members", stats['total_team_members'])
        st.metric("Avg Members per Team", 
                 f"{stats['total_team_members'] / stats['total_teams']:.1f}" if stats['total_teams'] > 0 else "0")
        
        # Team utilization
        if stats['total_teams'] > 0:
            utilization = (stats['total_team_members'] / (stats['total_teams'] * 5)) * 100
            st.metric("Team Capacity Utilization", f"{utilization:.1f}%")
    
    # Recent activity
    st.divider()
    st.subheader("🕒 Recent Activity")
    
    # Get recent registrations
    users = load_data(USERS_FILE)
    recent_users = []
    for username, data in users.items():
        if 'registered_at' in data:
            recent_users.append({
                'username': username,
                'role': data.get('role', 'Unassigned'),
                'registered_at': data['registered_at']
            })
    
    # Sort by registration date
    recent_users.sort(key=lambda x: x['registered_at'], reverse=True)
    
    if recent_users:
        st.write("**Recent Registrations:**")
        for user in recent_users[:5]:  # Show last 5
            reg_date = datetime.fromisoformat(user['registered_at']).strftime('%Y-%m-%d %H:%M')
            st.write(f"• {user['username']} - {user['role']} ({reg_date})")
    else:
        st.info("No recent activity to display.")

def main_app():
    st.title("TechDev Platform 🚀")
    
    # Sidebar with user info and navigation
    with st.sidebar:
        st.write(f"**Logged in as:** {st.session_state.username}")
        if st.session_state.user_role:
            role_emoji = "👨‍💼" if st.session_state.user_role == "Tech Lead" else "👨‍💻"
            st.write(f"**Role:** {role_emoji} {st.session_state.user_role}")
            
            if st.session_state.user_role == "Tech Lead" and st.session_state.tech_lead_verified:
                st.success("🔒 Verified")
        
        st.divider()
        
        # Navigation buttons
        if st.button("🏠 Dashboard"):
            st.session_state.current_page = "dashboard"
            st.rerun()
        
        if st.session_state.user_role == 'Developer Intern':
            if st.button("👥 My Team"):
                st.session_state.current_page = "team_management"
                st.rerun()
        
        elif st.session_state.user_role == 'Tech Lead' and st.session_state.tech_lead_verified:
            if st.button("🎛️ Manage All Teams"):
                st.session_state.current_page = "manage_all_teams"
                st.rerun()
            
            if st.button("📊 Analytics"):
                st.session_state.current_page = "platform_analytics"
                st.rerun()
        
        st.divider()
        
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content based on current page
    if st.session_state.current_page == "dashboard":
        user_dashboard()
    elif st.session_state.current_page == "tech_lead_registration":
        tech_lead_registration()
    elif st.session_state.current_page == "team_management":
        team_management_page()
    elif st.session_state.current_page == "manage_all_teams":
        manage_all_teams_page()
    elif st.session_state.current_page == "platform_analytics":
        platform_analytics_page()

def main():
    st.set_page_config(page_title="TechDev Platform", layout="wide", page_icon="🚀")
    init_session_state()

    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()