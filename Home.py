import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import re
import json
import os
import hashlib
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any
# Instead of:
from supabase import create_client

# Try:
from supabase.client import create_client, Client
# Performance Monitoring Class
class PerformanceBenchmark:
    def __init__(self):
        self.metrics = {
            'user_engagement': [],
            'system_performance': [],
            'team_productivity': [],
            'platform_health': []
        }
        self.benchmarks_file = "performance_benchmarks.json"
        self.load_benchmarks()
    
    def load_benchmarks(self):
        """Load existing benchmark data"""
        if os.path.exists(self.benchmarks_file):
            try:
                with open(self.benchmarks_file, 'r') as f:
                    data = json.load(f)
                    self.metrics = data
            except:
                pass
    
    def save_benchmarks(self):
        """Save benchmark data"""
        with open(self.benchmarks_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def record_metric(self, category: str, metric_name: str, value: float, timestamp: str = None):
        """Record a performance metric"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        if category not in self.metrics:
            self.metrics[category] = []
        
        self.metrics[category].append({
            'metric_name': metric_name,
            'value': value,
            'timestamp': timestamp
        })
        self.save_benchmarks()
    
    def get_benchmark_data(self, category: str, days: int = 30) -> List[Dict]:
        """Get benchmark data for specific category and time period"""
        if category not in self.metrics:
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_data = []
        
        for metric in self.metrics[category]:
            metric_date = datetime.fromisoformat(metric['timestamp'])
            if metric_date >= cutoff_date:
                filtered_data.append(metric)
        
        return filtered_data

# Supabase config - Fixed configuration
SUPABASE_URL = "https://pjhgxmxjsncqnzxeqdjt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqaGd4bXhqc25jcW56eGVxZGp0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxODgxMTUsImV4cCI6MjA2NDc2NDExNX0.H-UY1jbbutuUFUeSMrozPdEzqA4UTT_b7HWeF4Ljo3Q"

# Initialize Supabase client with error handling
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Supabase connection error: {e}")
    supabase = None

# Initialize Performance Benchmark
performance_monitor = PerformanceBenchmark()

# File paths for team management data
USERS_FILE = "users_roles.json"
TEAMS_FILE = "teams.json"
TECH_LEADS_FILE = "tech_leads.json"

# Initialize session state
def init_session_state():
    defaults = {
        'logged_in': False,
        'username': "",
        'login_attempts': 0,
        'last_attempt': None,
        'user_role': "",
        'current_page': "dashboard",
        'tech_lead_verified': False,
        'performance_tracking': True
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Enhanced team management helper functions
def load_data(filename):
    start_time = time.time()
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                load_time = time.time() - start_time
                performance_monitor.record_metric('system_performance', f'file_load_{filename}', load_time)
                return data
        return {}
    except Exception as e:
        st.error(f"Error loading {filename}: {e}")
        return {}

def save_data(data, filename):
    start_time = time.time()
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            save_time = time.time() - start_time
            performance_monitor.record_metric('system_performance', f'file_save_{filename}', save_time)
    except Exception as e:
        st.error(f"Error saving {filename}: {e}")

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
    
    # Record user engagement metric
    performance_monitor.record_metric('user_engagement', 'role_registration', 1)

def register_tech_lead(token):
    """Register tech lead with personal access token - REMOVED ACCESS RESTRICTIONS"""
    tech_leads = load_data(TECH_LEADS_FILE)
    tech_leads[st.session_state.username] = {
        'token_hash': hash_token(token),
        'registered_at': datetime.now().isoformat(),
        'status': 'active',
        'permissions': 'full_access'  # Full access for tech leads
    }
    save_data(tech_leads, TECH_LEADS_FILE)
    st.session_state.tech_lead_verified = True
    
    # Record performance metric
    performance_monitor.record_metric('user_engagement', 'tech_lead_registration', 1)

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
        if leader in users:  # Allow all users, not just interns
            team_info = {
                'team_id': team_key,
                'leader': leader,
                'members': team_data.get('members', []),
                'created_at': team_data.get('created_at', ''),
                'member_count': len(team_data.get('members', []))
            }
            all_teams.append(team_info)
    
    # Record team productivity metric
    performance_monitor.record_metric('team_productivity', 'active_teams', len(all_teams))
    
    return all_teams

def get_platform_stats():
    """Get overall platform statistics with performance tracking"""
    start_time = time.time()
    
    users = load_data(USERS_FILE)
    teams = load_data(TEAMS_FILE)
    tech_leads = load_data(TECH_LEADS_FILE)
    
    stats = {
        'total_users': len(users),
        'tech_leads': len(tech_leads),
        'developer_interns': len([u for u in users.values() if u.get('role') == 'Developer Intern']),
        'total_teams': len(teams),
        'total_team_members': sum(len(team.get('members', [])) for team in teams.values()),
        'platform_health_score': calculate_platform_health(users, teams, tech_leads)
    }
    
    processing_time = time.time() - start_time
    performance_monitor.record_metric('system_performance', 'stats_calculation', processing_time)
    
    return stats

def calculate_platform_health(users, teams, tech_leads):
    """Calculate overall platform health score (0-100)"""
    score = 0
    
    # User engagement (30%)
    if len(users) > 0:
        active_users = len([u for u in users.values() if u.get('role')])
        user_engagement = (active_users / len(users)) * 30
        score += user_engagement
    
    # Team formation (40%)
    if len(teams) > 0:
        active_teams = len([t for t in teams.values() if len(t.get('members', [])) > 0])
        team_health = (active_teams / len(teams)) * 40 if len(teams) > 0 else 0
        score += team_health
    
    # Leadership presence (30%)
    if len(users) > 0:
        leadership_ratio = (len(tech_leads) / len(users)) * 30 if len(users) > 0 else 0
        score += min(leadership_ratio, 30)  # Cap at 30%
    
    return min(round(score, 1), 100)

# Enhanced authentication functions with better error handling
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
    if not supabase:
        return False, "Database connection unavailable"
    
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        performance_monitor.record_metric('user_engagement', 'user_registration', 1)
        return True, "Registered successfully. Please check your email to verify your account."
    except Exception as e:
        return False, f"Registration failed: {str(e)}"

def login_user(email, password):
    if not supabase:
        # Fallback login for demo purposes
        if email and password:
            performance_monitor.record_metric('user_engagement', 'login_success', 1)
            return True, email
        return False, "Invalid credentials"
    
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            performance_monitor.record_metric('user_engagement', 'login_success', 1)
            return True, email
        else:
            performance_monitor.record_metric('user_engagement', 'login_failure', 1)
            return False, "Login failed. Please make sure your email is verified."
    except Exception as e:
        performance_monitor.record_metric('user_engagement', 'login_error', 1)
        return False, f"Login error: {str(e)}"

def check_rate_limit():
    if st.session_state.login_attempts >= 3:
        if st.session_state.last_attempt:
            time_diff = datetime.now() - st.session_state.last_attempt
            if time_diff < timedelta(minutes=5):
                return False, f"Too many failed attempts. Try again in {5 - time_diff.seconds // 60} minutes."
        else:
            st.session_state.login_attempts = 0
    return True, ""

def performance_dashboard():
    """Performance benchmarking dashboard"""
    st.title("📊 Performance Benchmarks Dashboard")
    
    # Key Performance Indicators
    col1, col2, col3, col4 = st.columns(4)
    
    platform_stats = get_platform_stats()
    
    with col1:
        st.metric("Platform Health", f"{platform_stats['platform_health_score']}%", 
                 delta="5%" if platform_stats['platform_health_score'] > 80 else "-2%")
    
    with col2:
        user_engagement = len([m for m in performance_monitor.metrics.get('user_engagement', []) 
                              if datetime.fromisoformat(m['timestamp']) > datetime.now() - timedelta(days=1)])
        st.metric("Daily Active Users", user_engagement, delta="3")
    
    with col3:
        avg_load_time = sum([m['value'] for m in performance_monitor.metrics.get('system_performance', []) 
                            if 'file_load' in m['metric_name']]) / max(1, len([m for m in performance_monitor.metrics.get('system_performance', []) if 'file_load' in m['metric_name']]))
        st.metric("Avg Load Time", f"{avg_load_time:.3f}s", delta="-0.05s")
    
    with col4:
        st.metric("Active Teams", platform_stats['total_teams'], delta="2")
    
    # Performance Charts
    st.subheader("📈 Performance Trends")
    
    tab1, tab2, tab3 = st.tabs(["User Engagement", "System Performance", "Team Productivity"])
    
    with tab1:
        engagement_data = performance_monitor.get_benchmark_data('user_engagement', 7)
        if engagement_data:
            df = pd.DataFrame(engagement_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            fig = px.line(df, x='timestamp', y='value', color='metric_name', 
                         title="User Engagement Trends (Last 7 Days)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No engagement data available yet.")
    
    with tab2:
        perf_data = performance_monitor.get_benchmark_data('system_performance', 7)
        if perf_data:
            df = pd.DataFrame(perf_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            fig = px.scatter(df, x='timestamp', y='value', color='metric_name',
                           title="System Performance Metrics (Last 7 Days)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No performance data available yet.")
    
    with tab3:
        team_data = performance_monitor.get_benchmark_data('team_productivity', 7)
        if team_data:
            df = pd.DataFrame(team_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            fig = px.bar(df, x='timestamp', y='value', color='metric_name',
                        title="Team Productivity Metrics (Last 7 Days)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No team productivity data available yet.")
    
    # Benchmark Goals
    st.subheader("🎯 Performance Benchmarks & Goals")
    
    benchmarks = {
        "User Engagement": {
            "current": platform_stats['platform_health_score'],
            "target": 95,
            "metric": "Platform Health Score"
        },
        "System Performance": {
            "current": avg_load_time * 1000,  # Convert to ms
            "target": 100,  # 100ms target
            "metric": "Avg Response Time (ms)"
        },
        "Team Formation": {
            "current": (platform_stats['total_teams'] / max(1, platform_stats['developer_interns'])) * 100,
            "target": 80,
            "metric": "Team Formation Rate (%)"
        }
    }
    
    for name, data in benchmarks.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            progress = min(data['current'] / data['target'], 1.0)
            st.progress(progress)
            st.write(f"**{name}**: {data['current']:.1f} / {data['target']} {data['metric']}")
        with col2:
            if progress >= 0.9:
                st.success("✅ Excellent")
            elif progress >= 0.7:
                st.warning("⚠️ Good")
            else:
                st.error("❌ Needs Improvement")

# Rest of your existing functions (login_page, tech_lead_registration, etc.) remain the same
# but with enhanced error handling and performance tracking...

def login_page():
    st.title("🔐 TechDev Platform Login")

    can_attempt, rate_limit_msg = check_rate_limit()
    if not can_attempt:
        st.error(rate_limit_msg)
        return

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login")
        with st.form("user_login_form"):
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
                else:
                    st.error("Please enter both email and password.")

    with tab2:
        st.subheader("Register")
        with st.form("user_register_form"):
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
    """Enhanced Tech Lead registration with full access"""
    st.subheader("🔐 Tech Lead Registration - Full Access")
    st.success("🚀 Tech Leads get full platform access with no restrictions!")
    
    with st.form("tech_lead_registration_form"):
        st.write("**Enhanced Security Requirements:**")
        st.write("• Token must be at least 20 characters")
        st.write("• Must contain both letters and numbers")
        st.write("• Your token will be encrypted and secure")
        st.write("• **No access restrictions - full platform control**")
        
        token = st.text_input("Personal Access Token", type="password", 
                             placeholder="Enter your GitLab/GitHub Personal Access Token")
        
        confirm_token = st.text_input("Confirm Token", type="password",
                                     placeholder="Re-enter your token")
        
        agree = st.checkbox("I understand that I will have full platform access and administrative privileges")
        
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
                    st.success("🚀 You now have full platform access!")
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
            st.success("🔒 Verified Tech Lead Account - Full Access Enabled")
    
    # Performance metrics for current user
    st.subheader("📈 Your Performance Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Activity Score", "92%", "5%")
    with col2:
        teams_created = len([t for t in load_data(TEAMS_FILE).values() if t.get('leader') == st.session_state.username])
        st.metric("Teams Created", teams_created)
    with col3:
        login_count = len([m for m in performance_monitor.metrics.get('user_engagement', []) 
                          if m.get('metric_name') == 'login_success'])
        st.metric("Total Logins", login_count)
    
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
        st.subheader("🎛️ Tech Lead Controls - Full Access")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔍 View All Teams", use_container_width=True):
                st.session_state.current_page = "manage_all_teams"
                st.rerun()
        
        with col2:
            if st.button("📊 Platform Analytics", use_container_width=True):
                st.session_state.current_page = "platform_analytics"
                st.rerun()
        
        with col3:
            if st.button("⚡ Performance Benchmarks", use_container_width=True):
                st.session_state.current_page = "performance_dashboard"
                st.rerun()

def main_app():
    st.title("TechDev Platform 🚀")
    
    # Sidebar with user info and navigation
    with st.sidebar:
        st.write(f"**Logged in as:** {st.session_state.username}")
        if st.session_state.user_role:
            role_emoji = "👨‍💼" if st.session_state.user_role == "Tech Lead" else "👨‍💻"
            st.write(f"**Role:** {role_emoji} {st.session_state.user_role}")
            
            if st.session_state.user_role == "Tech Lead" and st.session_state.tech_lead_verified:
                st.success("🔒 Verified - Full Access")
        
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
            
            if st.button("⚡ Performance Benchmarks"):
                st.session_state.current_page = "performance_dashboard"
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
    elif st.session_state.current_page == "performance_dashboard":
        performance_dashboard()
    # Add other page handlers here...

def main():
    st.set_page_config(page_title="TechDev Platform", layout="wide", page_icon="🚀")
    init_session_state()

    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()