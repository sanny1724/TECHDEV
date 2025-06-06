import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.title("🧑‍💻 Developer Standup Entry")

DATA_FILE = "developer_standup.csv"
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["Date", "Student ID", "Tasks Done", "What Learned"])

with st.form("standup_form"):
    student_id = st.text_input("🆔 Student ID")
    tasks_done = st.text_area("✅ Tasks Done")
    what_learned = st.text_area("📘 What You Learned")
    submitted = st.form_submit_button("📤 Submit")

    if submitted:
        new_entry = {
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Student ID": student_id,
            "Tasks Done": tasks_done,
            "What Learned": what_learned
        }
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("✅ Standup submitted successfully!")

st.subheader("📊 Previous Standup Entries")
st.dataframe(df.sort_values(by="Date", ascending=False))
