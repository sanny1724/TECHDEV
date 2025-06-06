import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import re
import json
import os
# pyright: ignore[reportMissingImports

# Supabase config
SUPABASE_URL = "https://pjhgxmxjsncqnzxeqdjt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqaGd4bXhqc25jcW56eGVxZGp0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxODgxMTUsImV4cCI6MjA2NDc2NDExNX0.H-UY1jbbutuUFUeSMrozPdEzqA4UTT_b7HWeF4Ljo3Q"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# File paths for team management data
USERS_FILE = "users_roles.json"
TEAMS_FILE = "teams.json"

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

def get_user_role():
    users = load_data(USERS_FILE)
    return users.get(st.session_state.username, {}).get('role', '')

def set_user_role(role):
    users = load_data(USERS_FILE)
    if st.session_state.username not in users:
        users[st.session_state.username] = {}
    users[st.session_state.username]['role'] = role
    save_data(users, USERS_FILE)
    st.session_state.user_role = role

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

def user_dashboard():
    st.header("📊 User Dashboard")
    st.success(f"Welcome, {st.session_state.username}")
    
    # Display current role if set
    if st.session_state.user_role:
        st.info(f"Current Role: {st.session_state.user_role}")
    
    # Role registration section
    st.subheader("🎯 Choose Your Role")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👨‍💼 Register as Tech Lead", use_container_width=True):
            set_user_role('Tech Lead')
            st.success("✅ Registered as Tech Lead!")
            st.rerun()
    
    with col2:
        if st.button("👨‍💻 Register as Developer Intern", use_container_width=True):
            set_user_role('Developer Intern')
            st.success("✅ Registered as Developer Intern!")
            st.rerun()
    
    # Show team management option for Developer Interns
    if st.session_state.user_role == 'Developer Intern':
        st.divider()
        st.subheader("👥 Team Management")
        if st.button("Manage Your Team", use_container_width=True):
            st.session_state.current_page = "team_management"
            st.rerun()
    
    # Original dashboard content
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
    
    # Navigation
    st.divider()
    if st.button("🏠 Back to Dashboard"):
        st.session_state.current_page = "dashboard"
        st.rerun()

def main_app():
    st.title("Welcome! 👋")
    
    # Sidebar with user info and navigation
    with st.sidebar:
        st.write(f"**Logged in as:** {st.session_state.username}")
        if st.session_state.user_role:
            st.write(f"**Role:** {st.session_state.user_role}")
        
        st.divider()
        
        # Navigation buttons
        if st.button("🏠 Dashboard"):
            st.session_state.current_page = "dashboard"
            st.rerun()
        
        if st.session_state.user_role == 'Developer Intern':
            if st.button("👥 Team Management"):
                st.session_state.current_page = "team_management"
                st.rerun()
        
        st.divider()
        
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content based on current page
    if st.session_state.current_page == "dashboard":
        user_dashboard()
    elif st.session_state.current_page == "team_management":
        team_management_page()

def main():
    st.set_page_config(page_title="TechDev Team Management", layout="wide")
    init_session_state()

    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()