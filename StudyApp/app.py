import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Study Anchor", layout="centered")
st.title("📅 Study Anchor Architect")

if 'exams' not in st.session_state:
    st.session_state.exams = []

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("➕ Add New Test")
    name = st.text_input("Subject Name")
    test_date = st.date_input("Test Date")
    difficulty = st.selectbox("Difficulty", ["1 (7 days)", "2 (10 days)", "3 (14 days)"])
    if st.button("Add to Schedule"):
        st.session_state.exams.append({"name": name, "date": test_date, "diff": difficulty[0]})

# --- Planning Logic ---
if st.session_state.exams:
    calendar_data = []
    diff_map = {"1": 7, "2": 10, "3": 14}
    
    # Sort by date
    sorted_exams = sorted(st.session_state.exams, key=lambda x: x['date'])
    occupied_dates = {}

    for exam in sorted_exams:
        total_days = diff_map[exam['diff']]
        sim_n = max(2, round(total_days * 0.2))
        prac_n = round(total_days * 0.3)
        study_n = total_days - sim_n - prac_n
        
        exam_summary = {"name": exam['name'], "date": exam['date'], "days": total_days, "phases": {}}
        
        # Anchor Simulations
        check_date = exam['date'] - timedelta(days=1)
        sim_dates = []
        while len(sim_dates) < sim_n:
            if check_date not in occupied_dates:
                occupied_dates[check_date] = f"SIM: {exam['name']}"
                sim_dates.append(check_date)
                calendar_data.append({"Date": check_date, "Subject": exam['name'], "Type": "Simulation"})
            check_date -= timedelta(days=1)
        exam_summary["phases"]["Simulations"] = sorted(sim_dates)

        # Fill Practice and Study
        for phase, count, label in [("Practice", prac_n, "Practice"), ("Study", study_n, "Study")]:
            p_dates = []
            while len(p_dates) < count:
                if check_date not in occupied_dates:
                    occupied_dates[check_date] = f"{label}: {exam['name']}"
                    p_dates.append(check_date)
                    calendar_data.append({"Date": check_date, "Subject": exam['name'], "Type": label})
                check_date -= timedelta(days=1)
            exam_summary["phases"][label] = sorted(p_dates)

        # --- Beautiful UI Display ---
        with st.container(border=True):
            st.subheader(f"{exam['name']} – {exam['date'].strftime('%d/%m')} (Level {exam['diff']})")
            st.caption(f"🏁 {total_days} days of preparation")
            
            for phase, dates in exam_summary["phases"].items():
                date_str = f"{dates[0].strftime('%d/%m')}–{dates[-1].strftime('%d/%m')}" if len(dates) > 1 else dates[0].strftime('%d/%m')
                pct = "20%" if phase == "Simulations" else "30%" if phase == "Practice" else "50%"
                st.write(f"**{phase} {pct}** – {date_str} ({len(dates)} days)")

    # --- CSV Export for Google Calendar ---
    st.divider()
    if calendar_data:
        export_df = pd.DataFrame(calendar_data)
        # Format for Google Calendar Import
        gcal_df = pd.DataFrame({
            'Subject': export_df['Subject'] + " (" + export_df['Type'] + ")",
            'Start Date': export_df['Date'],
            'All Day Event': True
        })
        csv = gcal_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download for Google Calendar", csv, "study_schedule.csv", "text/csv")