import streamlit as st
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
import re

# Initialize session state
def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'user_role' not in st.session_state:
        st.session_state.user_role = ""
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0
    if 'last_attempt' not in st.session_state:
        st.session_state.last_attempt = None

# Database functions
def init_database():
    """Initialize SQLite database with users table"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Create default admin user if not exists
    default_users = [
        ('admin', 'admin123', 'admin'),
        ('user', 'user123', 'user'),
        ('demo', 'demo123', 'user')
    ]
    
    for username, password, role in default_users:
        cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
        if not cursor.fetchone():
            salt = secrets.token_hex(16)
            password_hash = hash_password_with_salt(password, salt)
            cursor.execute('''
                INSERT INTO users (username, password_hash, salt, role)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, salt, role))
    
    conn.commit()
    conn.close()

def hash_password_with_salt(password, salt):
    """Hash password with salt"""
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

def verify_user(username, password):
    """Verify user credentials"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT password_hash, salt, role FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    
    if result:
        stored_hash, salt, role = result
        if stored_hash == hash_password_with_salt(password, salt):
            # Update last login
            cursor.execute('UPDATE users SET last_login = ? WHERE username = ?', 
                         (datetime.now(), username))
            conn.commit()
            conn.close()
            return True, role
    
    conn.close()
    return False, None

def is_valid_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    return True, "Password is valid"

def register_user(username, password, role='user'):
    """Register new user"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        salt = secrets.token_hex(16)
        password_hash = hash_password_with_salt(password, salt)
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, role)
            VALUES (?, ?, ?, ?)
        ''', (username, password_hash, salt, role))
        conn.commit()
        conn.close()
        return True, "User registered successfully"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username already exists"

def check_rate_limit():
    """Check if user has exceeded login attempts"""
    if st.session_state.login_attempts >= 3:
        if st.session_state.last_attempt:
            time_diff = datetime.now() - st.session_state.last_attempt
            if time_diff < timedelta(minutes=5):
                return False, f"Too many failed attempts. Try again in {5 - time_diff.seconds//60} minutes."
        else:
            st.session_state.login_attempts = 0
    return True, ""

def login_page():
    """Display login form"""
    st.title("🔐 Secure Login System")
    
    # Check rate limiting
    can_attempt, rate_limit_msg = check_rate_limit()
    
    if not can_attempt:
        st.error(rate_limit_msg)
        return
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to your account")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            remember_me = st.checkbox("Remember me")
            
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if username and password:
                    is_valid, role = verify_user(username, password)
                    if is_valid:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_role = role
                        st.session_state.login_attempts = 0
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.session_state.login_attempts += 1
                        st.session_state.last_attempt = datetime.now()
                        st.error(f"Invalid credentials. Attempt {st.session_state.login_attempts}/3")
                else:
                    st.error("Please enter both username and password")
    
    with tab2:
        st.subheader("Create new account")
        
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            register_button = st.form_submit_button("Register")
            
            if register_button:
                if new_username and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        is_valid, msg = is_valid_password(new_password)
                        if not is_valid:
                            st.error(msg)
                        else:
                            success, msg = register_user(new_username, new_password)
                            if success:
                                st.success(msg)
                            else:
                                st.error(msg)
                else:
                    st.error("Please fill in all fields")
    
    # Demo credentials info
    with st.expander("Demo Credentials"):
        st.write("**Available demo accounts:**")
        st.write("- Username: `admin`, Password: `admin123` (Admin)")
        st.write("- Username: `user`, Password: `user123` (User)")
        st.write("- Username: `demo`, Password: `demo123` (User)")

def admin_panel():
    """Admin-only panel"""
    st.header("👑 Admin Panel")
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # User management
    st.subheader("User Management")
    cursor.execute('SELECT username, role, created_at, last_login FROM users')
    users = cursor.fetchall()
    
    if users:
        import pandas as pd
        df = pd.DataFrame(users, columns=['Username', 'Role', 'Created', 'Last Login'])
        st.dataframe(df)
    
    conn.close()

def user_dashboard():
    """Regular user dashboard"""
    st.header("📊 User Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Profile Views", "1,234", "12%")
    
    with col2:
        st.metric("Posts", "56", "3%")
    
    with col3:
        st.metric("Followers", "789", "8%")
    
    st.subheader("Recent Activity")
    import pandas as pd
    import numpy as np
    
    # Sample data
    activity_data = pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=10),
        'Activity': np.random.randint(1, 100, 10)
    })
    
    st.line_chart(activity_data.set_index('Date'))

def main_app():
    """Main application after login"""
    st.title(f"Welcome, {st.session_state.username}! 👋")
    
    # Sidebar
    with st.sidebar:
        st.write(f"**User:** {st.session_state.username}")
        st.write(f"**Role:** {st.session_state.user_role}")
        
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Role-based content
    if st.session_state.user_role == 'admin':
        admin_panel()
    
    user_dashboard()

def main():
    """Main application"""
    st.set_page_config(
        page_title="Secure App",
        page_icon="🔐",
        layout="wide"
    )
    
    # Initialize
    init_session_state()
    init_database()
    
    # Route based on login status
    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()