import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Study Anchor", layout="centered")

# --- Chic Styling ---
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

# --- Sidebar ---
with st.sidebar:
    st.header("➕ Add New Test")
    name = st.text_input("Subject Name")
    test_date = st.date_input("Test Date")
    difficulty = st.selectbox("Difficulty", ["1 (7 days)", "2 (10 days)", "3 (14 days)"])
    if st.button("Add to Schedule"):
        st.session_state.exams.append({"name": name, "date": test_date, "diff": difficulty[0]})
    
    st.divider()
    if st.button("🗑️ Clear All Data"):
        st.session_state.exams = []
        st.session_state.manual_moves = {}
        st.rerun()

# --- Logic: Ironclad Simulation Reservation ---
if st.session_state.exams:
    calendar_data = []
    # This is the global vault that forbids ANY overlaps on simulation days
    global_simulation_vault = {} 
    
    diff_map = {"1": 7, "2": 10, "3": 14}
    # Sort by test date to give priority to the closest exams
    sorted_exams = sorted(st.session_state.exams, key=lambda x: x['date'])
    
    # STEP 1: Pre-calculate all Simulation days and LOCK them
    for exam in sorted_exams:
        total_days = diff_map[exam['diff']]
        sim_count = max(2, round(total_days * 0.2))
        
        # Start looking for sim days from the day before the test
        sim_check = exam['date'] - timedelta(days=1)
        placed_sims = 0
        while placed_sims < sim_count:
            # Task ID for manual overrides
            task_id = f"{exam['name']}_Simulation_{placed_sims}"
            
            if task_id in st.session_state.manual_moves:
                target_date = st.session_state.manual_moves[task_id]
            else:
                # Find the next truly empty day in the vault
                while sim_check in global_simulation_vault:
                    sim_check -= timedelta(days=1)
                target_date = sim_check
            
            # LOCK this date for this specific subject's simulation
            global_simulation_vault[target_date] = exam['name']
            
            calendar_data.append({
                "ID": task_id, "Date": target_date, "Subject": exam['name'],
                "Type": "Simulation", "Color": "#DC2626", "Pct": "20%",
                "IsMoved": task_id in st.session_state.manual_moves
            })
            sim_check -= timedelta(days=1)
            placed_sims += 1

    # STEP 2: Place Practice and Study tasks (allowing overlap with each other, but NOT with Simulations)
    for exam in sorted_exams:
        total_days = diff_map[exam['diff']]
        prac_n = round(total_days * 0.3)
        study_n = total_days - max(2, round(total_days * 0.2)) - prac_n
        
        check_date = exam['date'] - timedelta(days=1)
        
        for p_name, p_count, p_color, p_pct in [("Practice", prac_n, "#D97706", "30%"), ("Study", study_n, "#2563EB", "50%")]:
            placed = 0
            while placed < p_count:
                task_id = f"{exam['name']}_{p_name}_{placed}"
                
                if task_id in st.session_state.manual_moves:
                    final_date = st.session_state.manual_moves[task_id]
                else:
                    # Find a day that is NOT in the simulation vault
                    while check_date in global_simulation_vault:
                        check_date -= timedelta(days=1)
                    final_date = check_date
                
                calendar_data.append({
                    "ID": task_id, "Date": final_date, "Subject": exam['name'],
                    "Type": p_name, "Color": p_color, "Pct": p_pct,
                    "IsMoved": task_id in st.session_state.manual_moves
                })
                check_date -= timedelta(days=1)
                placed += 1

    # --- TABS ---
    tab1, tab2 = st.tabs(["📚 View by Subject", "📆 View by Date"])

    with tab1:
        for exam in st.session_state.exams:
            total_prep = diff_map[exam['diff']]
            with st.container(border=True):
                c_head, c_info = st.columns([2, 1])
                c_head.subheader(f"📘 {exam['name']}")
                c_info.write(f"**Goal:** {exam['date'].strftime('%d/%m')}")
                st.caption(f"Level {exam['diff']} — {total_prep} days prep")
                st.divider()
                
                sub_tasks = [d for d in calendar_data if d['Subject'] == exam['name']]
                cols = st.columns(3)
                for i, p_type in enumerate(["Simulation", "Practice", "Study"]):
                    p_tasks = sorted([d for d in sub_tasks if d['Type'] == p_type], key=lambda x: x['Date'])
                    if p_tasks:
                        with cols[i]:
                            st.caption(f"{p_type.upper()}")
                            d_start, d_end = p_tasks[0]['Date'].strftime('%d/%m'), p_tasks[-1]['Date'].strftime('%d/%m')
                            st.markdown(f"**{d_start}—{d_end}**")
                            st.write(f"_{len(p_tasks)} days_")

    with tab2:
        st.subheader("Your Daily Roadmap")
        with st.expander("🛠️ Personal Change (Move a Task)"):
            task_list = [f"{d['Date'].strftime('%d/%m')} - {d['Subject']} ({d['Type']})" for d in sorted(calendar_data, key=lambda x: x['Date'])]
            to_move = st.selectbox("Pick task:", task_list)
            selected_idx = task_list.index(to_move)
            target = sorted(calendar_data, key=lambda x: x['Date'])[selected_idx]
            new_date = st.date_input("Select new date:", target['Date'])
            if st.button("Save Move"):
                st.session_state.manual_moves[target['ID']] = new_date
                st.rerun()

        st.divider()
        df_roadmap = pd.DataFrame(calendar_data).sort_values("Date")
        for date, group in df_roadmap.groupby("Date"):
            st.markdown(f"#### {date.strftime('%A, %d %B')}")
            for _, row in group.iterrows():
                st.markdown(f"""
                    <div style="display: flex; align-items: center; background-color: white; padding: 12px; border-radius: 10px; border: 1px solid #F1F5F9; margin-bottom: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                        <div style="color: {row['Color']}; font-size: 1.2rem; margin-right: 15px; font-weight: bold;">✓</div>
                        <div>
                            <div style="color: #64748B; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">{row['Type']}</div>
                            <div style="color: #1E293B; font-size: 1rem; font-weight: 600;">{row['Subject']}</div>
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