"""
Step 1: Connect Data Sources
Multi-source connection with terminal output simulation
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="Connect Sources - EduSync AI",
    page_icon="🔗",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .step-indicator {
        background: #3b82f6;
        color: white !important;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 1rem;
    }
    .source-card {
        background: linear-gradient(135deg, #1e3a5f, #1e40af);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #3b82f6;
        margin: 0.5rem 0;
        color: #e2e8f0;
    }
    .source-card h4 { color: #f8fafc !important; margin: 0; }
    .source-card p { color: #cbd5e1 !important; margin: 0.25rem 0 0 0; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'connected_sources' not in st.session_state:
    st.session_state.connected_sources = []
if 'source_data' not in st.session_state:
    st.session_state.source_data = {}

# Legacy system configurations
LEGACY_SYSTEMS = {
    "COBOL Mainframe (Student Records)": {
        "icon": "🖥️", "port": "3270", "protocol": "TN3270",
        "tables": ["STUDENT-MASTER", "GRADE-RECORDS", "ENROLLMENT-FILE"],
        "records": 1250, "data_type": "students"
    },
    "FORTRAN System (Historical Grades)": {
        "icon": "📟", "port": "22", "protocol": "SSH/SFTP",
        "tables": ["STUDENT.DAT", "GRADES.DAT", "COURSES.DAT"],
        "records": 3800, "data_type": "grades"
    },
    "SQL Server (Current SIS)": {
        "icon": "🗄️", "port": "1433", "protocol": "TDS",
        "tables": ["dbo.Students", "dbo.Grades", "dbo.Enrollments"],
        "records": 2100, "data_type": "mixed"
    },
    "PostgreSQL (Attendance)": {
        "icon": "🐘", "port": "5432", "protocol": "PostgreSQL",
        "tables": ["attendance_daily", "attendance_period", "excuses"],
        "records": 45000, "data_type": "attendance"
    },
    "Oracle Database (District)": {
        "icon": "🔶", "port": "1521", "protocol": "Oracle Net",
        "tables": ["DISTRICT.STUDENTS", "DISTRICT.STAFF", "DISTRICT.SCHOOLS"],
        "records": 5200, "data_type": "district"
    },
    "CSV/Excel Files (Guardians)": {
        "icon": "📄", "port": "N/A", "protocol": "File",
        "tables": ["guardians.csv", "contacts.xlsx", "emergency.csv"],
        "records": 2800, "data_type": "guardians"
    },
    "REST API (LMS Integration)": {
        "icon": "🌐", "port": "443", "protocol": "HTTPS",
        "tables": ["/api/courses", "/api/sections", "/api/enrollments"],
        "records": 890, "data_type": "courses"
    },
}

st.markdown('<span class="step-indicator">Step 1: Connect Data Sources</span>', unsafe_allow_html=True)
st.markdown("### Connect to multiple data sources across your school district")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("#### Add a Data Source")

    source_type = st.selectbox("Select System Type", list(LEGACY_SYSTEMS.keys()))
    config = LEGACY_SYSTEMS[source_type]

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #422006, #78350f); border-radius: 12px; padding: 1rem; border-left: 4px solid #f59e0b; margin: 0.5rem 0;">
        <h4 style="color: #fef9c3 !important; margin: 0;">{config['icon']} {source_type}</h4>
        <p style="color: #fde68a !important; margin: 0.25rem 0;">Protocol: {config['protocol']} | Port: {config['port']} | ~{config['records']:,} records</p>
    </div>
    """, unsafe_allow_html=True)

    if "CSV" not in source_type and "REST" not in source_type:
        host = st.text_input("Host", value="db.school.edu")
        port = st.text_input("Port", value=config['port'])
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password", value="demo123")
    elif "REST" in source_type:
        api_url = st.text_input("API URL", value="https://sis.school.edu/api/v2")
        api_key = st.text_input("API Key", type="password", value="sk-demo-key")
    else:
        file_path = st.text_input("File Path", value="/data/imports/")

    if st.button("🔌 Connect to This Source", use_container_width=True, type="primary"):
        if source_type in st.session_state.connected_sources:
            st.warning(f"{source_type} is already connected!")
        else:
            progress = st.progress(0)
            status = st.empty()
            terminal = st.empty()

            terminal_style = "background: #0f172a; color: #22c55e; font-family: monospace; padding: 1rem; border-radius: 8px; font-size: 0.85rem; white-space: pre-wrap; border: 1px solid #334155;"
            output = ""

            steps = [
                (f"Connecting to {source_type}...", 15),
                ("Authenticating credentials...", 30),
                ("Establishing secure tunnel...", 45),
                ("Discovering schema...", 60),
                ("Enumerating tables...", 75),
                ("Validating access permissions...", 90),
                ("Connection established!", 100)
            ]

            for step_text, prog in steps:
                status.markdown(f"**{step_text}**")
                progress.progress(prog)
                output += f"[{datetime.now().strftime('%H:%M:%S')}] {step_text}\n"
                terminal.markdown(f'<div style="{terminal_style}">{output}</div>', unsafe_allow_html=True)
                time.sleep(0.3)

            output += f"\n[{datetime.now().strftime('%H:%M:%S')}] Found tables/endpoints:\n"
            for table in config['tables']:
                output += f"  → {table}\n"
            output += f"\n[{datetime.now().strftime('%H:%M:%S')}] Estimated records: {config['records']:,}\n"
            terminal.markdown(f'<div style="{terminal_style}">{output}</div>', unsafe_allow_html=True)

            st.session_state.connected_sources.append(source_type)
            st.session_state.source_data[source_type] = {
                "config": config,
                "connected_at": datetime.now().isoformat()
            }

            st.success(f"✅ Connected to {source_type}!")
            time.sleep(1)
            st.rerun()

with col2:
    st.markdown("#### Connected Sources")

    if not st.session_state.connected_sources:
        st.info("No sources connected yet. Add at least 2 sources to continue.")
    else:
        for src in st.session_state.connected_sources:
            cfg = LEGACY_SYSTEMS[src]
            col_a, col_b = st.columns([5, 1])
            with col_a:
                st.markdown(f"""
                <div class="source-card">
                    <h4>{cfg['icon']} {src}</h4>
                    <p>Tables: {', '.join(cfg['tables'][:2])}... | ~{cfg['records']:,} records</p>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                if st.button("❌", key=f"remove_{src}"):
                    st.session_state.connected_sources.remove(src)
                    if src in st.session_state.source_data:
                        del st.session_state.source_data[src]
                    st.rerun()

        total_records = sum(LEGACY_SYSTEMS[s]['records'] for s in st.session_state.connected_sources)
        st.markdown(f"**Total Sources: {len(st.session_state.connected_sources)}** | **Total Records: ~{total_records:,}**")

        st.markdown("---")
        st.markdown("#### Ready to proceed?")

        if len(st.session_state.connected_sources) >= 2:
            if st.button("➡️ Proceed to AI Analysis", use_container_width=True, type="primary"):
                # Load sample data
                sample_data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data")

                try:
                    students_df = pd.read_csv(os.path.join(sample_data_path, "dirty_students.csv"))
                    grades_df = pd.read_csv(os.path.join(sample_data_path, "legacy_grades.csv"), delimiter="|")
                    attendance_df = pd.read_csv(os.path.join(sample_data_path, "attendance_records.csv"))
                    guardians_df = pd.read_csv(os.path.join(sample_data_path, "guardians.csv"))
                    enrollments_df = pd.read_csv(os.path.join(sample_data_path, "enrollments.csv"))

                    st.session_state.students_data = students_df
                    st.session_state.grades_data = grades_df
                    st.session_state.attendance_data = attendance_df
                    st.session_state.guardians_data = guardians_df
                    st.session_state.enrollments_data = enrollments_df
                except Exception as e:
                    # Generate sample data if files don't exist
                    st.session_state.students_data = pd.DataFrame({
                        'student_id': [1001, 1002, 1003],
                        'first_name': ['John', 'Jane', 'Bob'],
                        'last_name': ['Smith', 'Doe', 'Johnson'],
                        'grade': [10, 11, 9],
                        'status': ['Active', 'Active', 'Active']
                    })

                st.session_state.step = 2
                st.switch_page("pages/2_🤖_AI_Analysis.py")
        else:
            st.warning("Please connect at least 2 data sources to continue.")

# Sidebar info
with st.sidebar:
    st.markdown("### 📊 Connection Summary")
    if st.session_state.connected_sources:
        for src in st.session_state.connected_sources:
            cfg = LEGACY_SYSTEMS[src]
            st.markdown(f"{cfg['icon']} **{src.split('(')[0].strip()}**")
    else:
        st.markdown("*No sources connected*")

    st.markdown("---")
    if st.button("🔄 Reset All Connections", use_container_width=True):
        st.session_state.connected_sources = []
        st.session_state.source_data = {}
        st.rerun()
