import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Study Anchor", layout="centered")

# Styling: Clean, Modern borders with standard Streamlit buttons
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white; border-radius: 12px;
        border: 1px solid #E2E8F0; padding: 25px; margin-bottom: 20px;
    }
    h1, h2, h3 { color: #0e1117; font-family: sans-serif; }
    </style>
    """, unsafe_allow_html=True)

st.title("📅 Study Anchor Architect")

if 'exams' not in st.session_state: st.session_state.exams = []
if 'manual_moves' not in st.session_state: st.session_state.manual_moves = {}

# --- Sidebar: Add Exams ---
with st.sidebar:
    st.header("➕ Add New Test")
    name = st.text_input("Subject Name")
    test_date = st.date_input("Test Date")
    difficulty = st.selectbox("Difficulty", ["1 (7 days)", "2 (10 days)", "3 (14 days)"])
    if st.button("Add to Schedule"):
        st.session_state.exams.append({"name": name, "date": test_date, "diff": difficulty[0]})
    
    st.divider()
    if st.button("🗑️ Reset Everything"):
        st.session_state.exams = []
        st.session_state.manual_moves = {}
        st.rerun()

# --- Logic: Generate the Roadmap ---
if st.session_state.exams:
    calendar_data = []
    diff_map = {"1": 7, "2": 10, "3": 14}
    
    for exam in st.session_state.exams:
        total_days = diff_map[exam['diff']]
        sim_n, prac_n = max(2, round(total_days * 0.2)), round(total_days * 0.3)
        study_n = total_days - sim_n - prac_n
        
        check_date = exam['date'] - timedelta(days=1)
        # We store percentages here to show them in the Subject View
        phases = [("Simulation", sim_n, "🔴", "20%"), ("Practice", prac_n, "🟡", "30%"), ("Study", study_n, "🔵", "50%")]
        
        for phase, count, label, pct in phases:
            for i in range(count):
                task_id = f"{exam['name']}_{phase}_{i}"
                final_date = st.session_state.manual_moves.get(task_id, check_date)
                
                calendar_data.append({
                    "ID": task_id, "Date": final_date, "Subject": exam['name'],
                    "Type": phase, "Label": label, "Pct": pct,
                    "IsMoved": task_id in st.session_state.manual_moves
                })
                check_date -= timedelta(days=1)

    # --- TABS ---
    tab1, tab2 = st.tabs(["📚 View by Subject", "📆 View by Date"])

    with tab1:
        for exam in st.session_state.exams:
            with st.container(border=True):
                # Using columns to create a "Dashboard Header"
                header_col, info_col = st.columns([2, 1])
                with header_col:
                    st.markdown(f"### 📘 {exam['name']}")
                with info_col:
                    st.markdown(f"**Goal:** {exam['date'].strftime('%d/%m')}")

                st.divider() # Adds a clean thin line

                # Using columns for the 3 phases to make it look like a "Scorecard"
                c1, c2, c3 = st.columns(3)
                sub_tasks = [d for d in calendar_data if d['Subject'] == exam['name']]
                
                cols = [c1, c2, c3]
                for i, phase in enumerate(["Simulation", "Practice", "Study"]):
                    p_tasks = sorted([d for d in sub_tasks if d['Type'] == phase], key=lambda x: x['Date'])
                    if p_tasks:
                        with cols[i]:
                            st.caption(f"{phase.upper()} ({p_tasks[0]['Pct']})")
                            d_start = p_tasks[0]['Date'].strftime('%d/%m')
                            d_end = p_tasks[-1]['Date'].strftime('%d/%m')
                            st.markdown(f"**{d_start} — {d_end}**")
                            st.write(f"_{len(p_tasks)} days_")

    with tab2:
        st.subheader("Your Daily Roadmap")
        
        with st.expander("🛠️ Need to reschedule a specific day?"):
            task_list = [f"{d['Date'].strftime('%d/%m')} - {d['Subject']} ({d['Type']})" for d in calendar_data]
            to_move = st.selectbox("Pick the task to change:", task_list)
            selected_idx = task_list.index(to_move)
            target = calendar_data[selected_idx]
            new_date = st.date_input("Select new date:", target['Date'])
            if st.button("Save Personal Change"):
                st.session_state.manual_moves[target['ID']] = new_date
                st.rerun()

        st.divider()
        
        # Defining our Chic Color Palette
        check_colors = {
            "Simulation": "#DC2626", # Crimson
            "Practice": "#D97706",   # Amber
            "Study": "#2563EB"        # Royal Blue
        }

        df = pd.DataFrame(calendar_data).sort_values("Date")
        for date, group in df.groupby("Date"):
            st.markdown(f"#### {date.strftime('%A, %d %B')}")
            
            for _, row in group.iterrows():
                color = check_colors.get(row['Type'], "#64748B")
                
                # The Chic Checkmark Card
                st.markdown(f"""
                    <div style="
                        display: flex;
                        align-items: center;
                        background-color: white;
                        padding: 12px;
                        border-radius: 10px;
                        border: 1px solid #F1F5F9;
                        margin-bottom: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
                    ">
                        <div style="color: {color}; font-size: 1.2rem; margin-right: 15px; font-weight: bold;">✓</div>
                        <div>
                            <div style="color: #64748B; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">
                                {row['Type']}
                            </div>
                            <div style="color: #1E293B; font-size: 1rem; font-weight: 500;">
                                {row['Subject']}
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    # --- CSV Export ---
    st.divider()
    csv_df = pd.DataFrame(calendar_data)
    gcal_df = pd.DataFrame({
        'Subject': "[" + csv_df['Subject'].str.upper() + "] " + csv_df['Type'],
        'Start Date': csv_df['Date'], 'All Day Event': True
    })
    st.download_button("📥 Download for Google Calendar", gcal_df.to_csv(index=False).encode('utf-8'), "study_plan.csv", "text/csv")