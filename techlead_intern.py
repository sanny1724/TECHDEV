import streamlit as st

st.title("👨‍💼 Techlead Team Dashboard")

# Placeholder
st.markdown("🛠️ Waiting for team structure input...")

# Example layout (replace once you provide team data)
example_teams = {
    "Team Alpha": ["Alice", "Bob", "Charlie", "David", "Eve"],
    "Team Beta": ["Frank", "Grace", "Heidi", "Ivan", "Judy"]
}

for team_name, members in example_teams.items():
    with st.expander(team_name):
        for dev in members:
            st.write(f"👨‍💻 {dev}")
