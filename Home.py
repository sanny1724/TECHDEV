import streamlit as st
import pandas as pd
from datetime import datetime

# Initialize session state for navigation
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# Navigation function
def go_to_page(page_name):
    st.session_state.page = page_name
    st.rerun()

# Get current page from session state
page = st.session_state.page

# ---------------- HOME PAGE ----------------
if page == "home":
    st.set_page_config(page_title="Standup App", page_icon="👋")
    st.title("👋 Welcome to Standup App")
    st.markdown("### Choose your role:")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🧑‍💻 Developer")
        st.markdown("Submit your daily standup updates")
        if st.button("Enter as Developer", key="dev_btn", use_container_width=True):
            go_to_page("developer")
    
    with col2:
        st.markdown("#### 👨‍💼 Tech Lead")
        st.markdown("View team progress and updates")
        if st.button("Enter as Tech Lead", key="lead_btn", use_container_width=True):
            go_to_page("techlead")

# ---------------- DEVELOPER PAGE ----------------
elif page == "developer":
    st.set_page_config(page_title="Developer Standup", page_icon="🧑‍💻")
    
    # Back button in sidebar
    with st.sidebar:
        if st.button("⬅️ Back to Home", key="back_dev"):
            go_to_page("home")
    
    st.title("🧑‍💻 Developer Standup")
    st.markdown("---")
    
    # Developer standup form
    with st.form("standup_form"):
        st.subheader("📝 Daily Standup Form")
        
        # Basic info
        col1, col2 = st.columns(2)
        with col1:
            developer_name = st.text_input("👤 Your Name", placeholder="Enter your name")
        with col2:
            date_today = st.date_input("📅 Date", value=datetime.now().date())
        
        # Standup questions
        st.markdown("#### What did you work on yesterday?")
        yesterday_work = st.text_area(
            "Yesterday's Tasks",
            placeholder="Describe what you accomplished yesterday...",
            height=100
        )
        
        st.markdown("#### What will you work on today?")
        today_plan = st.text_area(
            "Today's Plan",
            placeholder="What are you planning to work on today?",
            height=100
        )
        
        st.markdown("#### Any blockers or challenges?")
        blockers = st.text_area(
            "Blockers/Challenges",
            placeholder="Any issues that are preventing you from moving forward?",
            height=80
        )
        
        # Additional fields
        col3, col4 = st.columns(2)
        with col3:
            mood = st.select_slider(
                "😊 How are you feeling?",
                options=["😫 Stressed", "😐 Okay", "😊 Good", "🚀 Excellent"],
                value="😊 Good"
            )
        with col4:
            priority = st.selectbox(
                "🎯 Today's Priority Level",
                ["Low", "Medium", "High", "Critical"]
            )
        
        # Submit button
        submitted = st.form_submit_button("📤 Submit Standup", use_container_width=True)
        
        if submitted:
            if developer_name and yesterday_work and today_plan:
                st.success("✅ Standup submitted successfully!")
                st.balloons()
                
                # Display confirmation
                with st.expander("📋 Your Submission Summary"):
                    st.write(f"**Name:** {developer_name}")
                    st.write(f"**Date:** {date_today}")
                    st.write(f"**Yesterday:** {yesterday_work}")
                    st.write(f"**Today:** {today_plan}")
                    st.write(f"**Blockers:** {blockers if blockers else 'None'}")
                    st.write(f"**Mood:** {mood}")
                    st.write(f"**Priority:** {priority}")
            else:
                st.error("❌ Please fill in at least Name, Yesterday's work, and Today's plan")

# ---------------- TECHLEAD PAGE ----------------
elif page == "techlead":
    st.set_page_config(page_title="Tech Lead Dashboard", page_icon="👨‍💼")
    
    # Back button in sidebar
    with st.sidebar:
        if st.button("⬅️ Back to Home", key="back_lead"):
            go_to_page("home")
        
        st.markdown("---")
        st.markdown("### 🔧 Dashboard Controls")
        
        # Filter options
        date_filter = st.date_input("📅 Filter by Date", value=datetime.now().date())
        
        team_filter = st.multiselect(
            "👥 Filter by Team Members",
            ["Alice Johnson", "Bob Smith", "Carol Davis", "David Wilson"],
            default=["Alice Johnson", "Bob Smith", "Carol Davis", "David Wilson"]
        )
    
    st.title("👨‍💼 Tech Lead Dashboard")
    st.markdown("---")
    
    # Sample data (in real app, this would come from database)
    sample_standups = [
        {
            "name": "Alice Johnson",
            "date": "2025-06-04",
            "yesterday": "Completed user authentication module, fixed 3 bugs in login system",
            "today": "Start working on password reset functionality",
            "blockers": "Need API documentation for third-party service",
            "mood": "😊 Good",
            "priority": "High"
        },
        {
            "name": "Bob Smith", 
            "date": "2025-06-04",
            "yesterday": "Implemented database migration scripts, updated user model",
            "today": "Work on data validation and error handling",
            "blockers": "None",
            "mood": "🚀 Excellent",
            "priority": "Medium"
        },
        {
            "name": "Carol Davis",
            "date": "2025-06-04", 
            "yesterday": "Designed new UI components, created wireframes",
            "today": "Implement responsive design for mobile devices",
            "blockers": "Waiting for design approval from client",
            "mood": "😐 Okay",
            "priority": "High"
        }
    ]
    
    # Team overview metrics
    st.subheader("📊 Team Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Team Members", len(sample_standups))
    with col2:
        blocked_count = sum(1 for s in sample_standups if s['blockers'] != "None")
        st.metric("🚫 Blocked Tasks", blocked_count)
    with col3:
        high_priority = sum(1 for s in sample_standups if s['priority'] == "High")
        st.metric("🔴 High Priority", high_priority)
    with col4:
        excellent_mood = sum(1 for s in sample_standups if "🚀" in s['mood'])
        st.metric("🚀 Excellent Mood", excellent_mood)
    
    st.markdown("---")
    
    # Display standups
    st.subheader("📋 Today's Standups")
    
    for standup in sample_standups:
        if standup['name'] in team_filter:
            with st.expander(f"👤 {standup['name']} - {standup['mood']}", expanded=True):
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.markdown(f"**📅 Date:** {standup['date']}")
                    st.markdown(f"**✅ Yesterday:** {standup['yesterday']}")
                    st.markdown(f"**🎯 Today:** {standup['today']}")
                    
                    if standup['blockers'] != "None":
                        st.markdown(f"**🚫 Blockers:** :red[{standup['blockers']}]")
                    else:
                        st.markdown(f"**🚫 Blockers:** :green[None]")
                
                with col_right:
                    st.markdown(f"**😊 Mood:** {standup['mood']}")
                    st.markdown(f"**🎯 Priority:** {standup['priority']}")
                    
                    # Action buttons
                    if standup['blockers'] != "None":
                        if st.button(f"🆘 Help {standup['name'].split()[0]}", key=f"help_{standup['name']}"):
                            st.info(f"Reaching out to help {standup['name']} with their blockers...")
    
    # Summary section
    st.markdown("---")
    st.subheader("📈 Team Summary")
    
    # Create summary charts/stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎯 Priority Distribution:**")
        priority_counts = {}
        for standup in sample_standups:
            priority = standup['priority']
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        for priority, count in priority_counts.items():
            st.write(f"- {priority}: {count}")
    
    with col2:
        st.markdown("**😊 Team Mood:**")
        mood_counts = {}
        for standup in sample_standups:
            mood = standup['mood']
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
        
        for mood, count in mood_counts.items():
            st.write(f"- {mood}: {count}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Standup App v1.0 | Built with Streamlit 💙"
    "</div>", 
    unsafe_allow_html=True
)