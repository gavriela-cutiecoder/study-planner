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
    .stCheckbox label p { font-size: 1rem; font-weight: 600; color: #1E293B; }
    .countdown-box {
        background-color: #EEF2FF;
        border: 1px solid #C7D2FE;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📅 Study Anchor Architect")

# Initialize Session State
if 'exams' not in st.session_state: st.session_state.exams = []
if 'manual_moves' not in st.session_state: st.session_state.manual_moves = {}
if 'completed_tasks' not in st.session_state: st.session_state.completed_tasks = {}

# --- NEW: Goal Countdown Logic ---
if st.session_state.exams:
    # Find the earliest exam date
    earliest_exam = min(st.session_state.exams, key=lambda x: x['date'])
    days_left = (earliest_exam['date'] - datetime.now().date()).days
    
    if days_left > 0:
        st.markdown(f"""
            <div class="countdown-box">
                <span style="color: #4338CA; font-weight: 700; font-size: 1.1rem;">
                    🚀 {days_left} Days until your {earliest_exam['name']} exam!
                </span>
            </div>
        """, unsafe_allow_html=True)
    elif days_left == 0:
        st.markdown(f"""<div class="countdown-box"><span style="color: #DC2626; font-weight: 700;">🔥 It's Exam Day for {earliest_exam['name']}! Good luck!</span></div>""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.header("➕ Add New Test")
    with st.form("add_test_form", clear_on_submit=True):
        name = st.text_input("Subject Name")
        test_date = st.date_input("Test Date")
        difficulty = st.selectbox("Difficulty", ["1 (7 days)", "2 (10 days)", "3 (14 days)"])
        submit = st.form_submit_button("Add to Schedule")
        
        if submit and name:
            if not any(e['name'].lower() == name.lower() for e in st.session_state.exams):
                st.session_state.exams.append({"name": name, "date": test_date, "diff": difficulty[0]})
                st.rerun()
    
    st.divider()
    if st.button("🗑️ Full Data Wipe"):
        st.session_state.clear()
        st.rerun()

# --- Logic: The "Strict Step" Scheduler ---
def build_clean_roadmap():
    fresh_list = []
    vault = {} 
    diff_map = {"1": 7, "2": 10, "3": 14}
    if not st.session_state.exams: return []
    sorted_exams = sorted(st.session_state.exams, key=lambda x: (int(x['diff']), x['date']), reverse=True)
    
    # 1. Place Simulations
    for exam in sorted_exams:
        sim_count = max(2, round(diff_map[exam['diff']] * 0.2))
        sim_check = exam['date'] - timedelta(days=1)
        for i in range(sim_count):
            task_id = f"{exam['name']}_Simulation_{i}"
            target_date = st.session_state.manual_moves.get(task_id, None)
            if not target_date:
                while sim_check in vault: sim_check -= timedelta(days=1)
                target_date = sim_check
                sim_check -= timedelta(days=1)
            vault[target_date] = 'sim'
            fresh_list.append({"ID": task_id, "Date": target_date, "Subject": exam['name'], "Type": "Simulation", "Color": "#DC2626", "IsPriority": int(exam['diff']) == 3})

    # 2. Place Practice/Study
    for exam in sorted_exams:
        total = diff_map[exam['diff']]
        p_n, s_n = round(total * 0.3), total - max(2, round(total * 0.2)) - round(total * 0.3)
        check_date = exam['date'] - timedelta(days=1)
        course_dates = []
        for p_name, p_count, p_color in [("Practice", p_n, "#D97706"), ("Study", s_n, "#2563EB")]:
            for i in range(p_count):
                task_id = f"{exam['name']}_{p_name}_{i}"
                final_date = st.session_state.manual_moves.get(task_id, None)
                if not final_date:
                    while True:
                        curr_v = vault.get(check_date, 0)
                        already_has_subject = any(d['Date'] == check_date and d['Subject'] == exam['name'] for d in fresh_list)
                        if curr_v != 'sim' and curr_v < 2 and not already_has_subject: break
                        check_date -= timedelta(days=1)
                    final_date = check_date
                if final_date not in vault: vault[final_date] = 1
                elif vault[final_date] != 'sim': vault[final_date] += 1
                fresh_list.append({"ID": task_id, "Date": final_date, "Subject": exam['name'], "Type": p_name, "Color": p_color, "IsPriority": int(exam['diff']) == 3})
                course_dates.append(final_date)
                check_date -= timedelta(days=1)

        # 3. Refresh Logic
        course_dates.sort()
        for i in range(len(course_dates) - 1):
            gap = (course_dates[i+1] - course_dates[i]).days
            if gap > 7:
                ref_date = course_dates[i] + timedelta(days=gap // 2)
                while vault.get(ref_date) == 'sim' and ref_date < course_dates[i+1]: ref_date += timedelta(days=1)
                if ref_date < course_dates[i+1] and vault.get(ref_date) != 'sim':
                    fresh_list.append({"ID": f"{exam['name']}_Refresh_{i}", "Date": ref_date, "Subject": exam['name'], "Type": "Refresh", "Color": "#10B981", "IsPriority": False})
    return fresh_list

calendar_data = build_clean_roadmap()

# --- TABS ---
tab1, tab2 = st.tabs(["📚 View by Subject", "📆 View by Date"])

with tab1:
    for exam in st.session_state.exams:
        with st.container(border=True):
            st.subheader(f"📘 {exam['name']} — {exam['date'].strftime('%d/%m')}")
            st.divider()
            sub = [d for d in calendar_data if d['Subject'] == exam['name']]
            cols = st.columns(4)
            for i, pt in enumerate(["Simulation", "Practice", "Study", "Refresh"]):
                pts = sorted([d for d in sub if d['Type'] == pt], key=lambda x: x['Date'])
                if pts:
                    with cols[i]:
                        st.caption(pt.upper())
                        st.markdown(f"**{pts[0]['Date'].strftime('%d/%m')}**")

with tab2:
    if calendar_data:
        df_display = pd.DataFrame(calendar_data).sort_values("Date")
        for date, group in df_display.groupby("Date"):
            st.markdown(f"#### {date.strftime('%A, %d %B')}")
            for _, row in group.iterrows():
                with st.container(border=True):
                    cols = st.columns([0.1, 0.9])
                    is_done = st.session_state.completed_tasks.get(row['ID'], False)
                    if cols[0].checkbox("", value=is_done, key=f"f_{row['ID']}"):
                        st.session_state.completed_tasks[row['ID']] = True
                    else: st.session_state.completed_tasks[row['ID']] = False
                    with cols[1]:
                        priority = " ⭐" if row['IsPriority'] else ""
                        st.markdown(f"<span style='color:{row['Color']}; font-size:0.7rem; font-weight:700; text-transform:uppercase;'>{row['Type']}{priority}</span>", unsafe_allow_html=True)
                        st.markdown(f"**{row['Subject']}**")