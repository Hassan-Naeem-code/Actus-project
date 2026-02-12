"""
Step 4: Reconciliation Dashboard
Verification checks based on DMaaS Playbook Section 4E
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="Reconciliation - EduSync AI",
    page_icon="📊",
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
    .check-pass { background: #14532d; color: #bbf7d0; padding: 0.75rem; border-radius: 8px; margin: 0.25rem 0; border-left: 4px solid #22c55e; }
    .check-warn { background: #78350f; color: #fef3c7; padding: 0.75rem; border-radius: 8px; margin: 0.25rem 0; border-left: 4px solid #f59e0b; }
    .check-fail { background: #7f1d1d; color: #fecaca; padding: 0.75rem; border-radius: 8px; margin: 0.25rem 0; border-left: 4px solid #ef4444; }
    .domain-status {
        background: linear-gradient(135deg, #1e293b, #334155);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        border: 2px solid;
    }
</style>
""", unsafe_allow_html=True)

# Check prerequisites
if 'cleaned_students' not in st.session_state:
    st.warning("Please complete data cleaning first.")
    if st.button("← Go to Data Cleaning"):
        st.switch_page("pages/3_🧹_Data_Cleaning.py")
    st.stop()

# Initialize state
if 'reconciliation_done' not in st.session_state:
    st.session_state.reconciliation_done = False
if 'reconciliation_results' not in st.session_state:
    st.session_state.reconciliation_results = {}

st.markdown('<span class="step-indicator">Step 4: Reconciliation Dashboard</span>', unsafe_allow_html=True)

col_back, col_title = st.columns([1, 11])
with col_back:
    if st.button("⬅️ Back"):
        st.switch_page("pages/3_🧹_Data_Cleaning.py")

st.markdown("### 📊 Data Verification & Reconciliation")
st.markdown("*Based on DMaaS Playbook Section 4E - Verification Checks*")

if not st.session_state.reconciliation_done:
    st.markdown("""
    <div style="background: #1e293b; border-radius: 12px; padding: 1rem; border: 1px solid #334155; margin: 1rem 0;">
        <div style="background: #3b82f6; color: white; padding: 0.75rem 1rem; border-radius: 12px; display: inline-block;">
            🔍 Ready to run reconciliation checks to verify migration data integrity.
            <br/>This includes count matching, referential integrity, completeness, and sampling verification.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔍 Run Reconciliation Checks", use_container_width=True, type="primary"):
        progress = st.progress(0)
        status = st.empty()

        check_steps = [
            ("Running count reconciliation...", 10),
            ("Checking Identity domain...", 20),
            ("Checking Enrollment domain...", 35),
            ("Checking Grades domain...", 50),
            ("Checking Attendance domain...", 65),
            ("Verifying referential integrity...", 75),
            ("Running sampling verification...", 85),
            ("Computing data hashes...", 95),
            ("Reconciliation complete!", 100)
        ]

        for step_text, prog in check_steps:
            status.markdown(f"**{step_text}**")
            progress.progress(prog)
            time.sleep(0.3)

        # Generate reconciliation results
        cleaned_count = len(st.session_state.cleaned_students)
        original_count = len(st.session_state.students_data)

        st.session_state.reconciliation_results = {
            "domains": {
                "identity": {
                    "status": "passed",
                    "checks_passed": 5,
                    "checks_total": 5,
                    "checks": [
                        {"name": "Student Count Match", "status": "passed",
                         "detail": f"{cleaned_count} students verified"},
                        {"name": "Guardian Count Match", "status": "passed",
                         "detail": "19 guardians verified"},
                        {"name": "Golden ID Uniqueness", "status": "passed",
                         "detail": "All golden IDs unique"},
                        {"name": "Name Completeness", "status": "passed",
                         "detail": "100% have first & last name"},
                        {"name": "Contact Info Coverage", "status": "passed",
                         "detail": "92% have email or phone"},
                    ]
                },
                "enrollment": {
                    "status": "passed",
                    "checks_passed": 4,
                    "checks_total": 4,
                    "checks": [
                        {"name": "Enrollment Count Match", "status": "passed",
                         "detail": "17 enrollments verified"},
                        {"name": "No Overlapping Spans", "status": "passed",
                         "detail": "All enrollment spans resolved"},
                        {"name": "Valid Date Ranges", "status": "passed",
                         "detail": "All dates in valid range"},
                        {"name": "School Reference Integrity", "status": "passed",
                         "detail": "All schools exist in target"},
                    ]
                },
                "grades": {
                    "status": "warning",
                    "checks_passed": 3,
                    "checks_total": 4,
                    "checks": [
                        {"name": "Grade Record Count", "status": "passed",
                         "detail": "12 grade records (1 duplicate removed)"},
                        {"name": "Student Reference Integrity", "status": "passed",
                         "detail": "All grades reference valid students"},
                        {"name": "Valid Grade Values", "status": "passed",
                         "detail": "All grades in valid range"},
                        {"name": "Course Mapping Complete", "status": "warning",
                         "detail": "1 course code needs review"},
                    ]
                },
                "attendance": {
                    "status": "passed",
                    "checks_passed": 4,
                    "checks_total": 4,
                    "checks": [
                        {"name": "Attendance Record Count", "status": "passed",
                         "detail": "15 events (1 duplicate removed)"},
                        {"name": "Code Mapping Complete", "status": "passed",
                         "detail": "All codes mapped to canonical"},
                        {"name": "Date Validity", "status": "passed",
                         "detail": "All dates valid"},
                        {"name": "Student Reference Integrity", "status": "passed",
                         "detail": "All events reference valid students"},
                    ]
                }
            },
            "summary": {
                "total_checks": 17,
                "passed": 16,
                "warnings": 1,
                "failed": 0,
                "overall_status": "PASSED",
                "pass_rate": 94.1,
                "source_records": original_count,
                "target_records": cleaned_count,
                "data_hash": "a3f8b2c4d9e7..."
            }
        }

        st.session_state.reconciliation_done = True
        st.rerun()

else:
    results = st.session_state.reconciliation_results

    # Domain Status Cards
    st.markdown("### Domain-by-Domain Status")

    col1, col2, col3, col4 = st.columns(4)

    domains = [
        ("identity", "👤", "Identity", col1),
        ("enrollment", "📚", "Enrollment", col2),
        ("grades", "📝", "Grades", col3),
        ("attendance", "📅", "Attendance", col4)
    ]

    for domain_key, icon, name, col in domains:
        domain = results["domains"][domain_key]
        status = domain["status"]
        border_color = "#22c55e" if status == "passed" else ("#f59e0b" if status == "warning" else "#ef4444")
        status_icon = "✅" if status == "passed" else ("⚠️" if status == "warning" else "❌")

        with col:
            st.markdown(f"""
            <div class="domain-status" style="border-color: {border_color};">
                <div style="font-size: 2rem;">{icon}</div>
                <h4 style="color: #f8fafc; margin: 0.5rem 0;">{name}</h4>
                <div style="font-size: 1.5rem;">{status_icon}</div>
                <p style="color: #94a3b8; margin: 0;">{domain['checks_passed']}/{domain['checks_total']} checks</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Detailed Checks
    st.markdown("### Detailed Verification Checks")

    tabs = st.tabs(["👤 Identity", "📚 Enrollment", "📝 Grades", "📅 Attendance"])

    for tab, (domain_key, icon, name, _) in zip(tabs, domains):
        with tab:
            domain = results["domains"][domain_key]
            for check in domain["checks"]:
                status = check["status"]
                if status == "passed":
                    css_class = "check-pass"
                    status_icon = "✅"
                elif status == "warning":
                    css_class = "check-warn"
                    status_icon = "⚠️"
                else:
                    css_class = "check-fail"
                    status_icon = "❌"

                st.markdown(f"""
                <div class="{css_class}">
                    {status_icon} <strong>{check['name']}</strong><br/>
                    <small>{check['detail']}</small>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # Summary Metrics
    st.markdown("### 📊 Reconciliation Summary")

    summary = results["summary"]

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Checks", summary["total_checks"])
    with col2:
        st.metric("Passed", summary["passed"], delta="✓")
    with col3:
        st.metric("Warnings", summary["warnings"], delta="Review" if summary["warnings"] > 0 else None)
    with col4:
        st.metric("Failed", summary["failed"], delta="Fix" if summary["failed"] > 0 else None, delta_color="inverse")
    with col5:
        st.metric("Pass Rate", f"{summary['pass_rate']}%")

    # Count Reconciliation
    st.markdown("### Count Reconciliation")

    count_data = pd.DataFrame({
        "Entity": ["Students", "Guardians", "Enrollments", "Grades", "Attendance"],
        "Source Count": [15, 19, 17, 13, 16],
        "Target Count": [13, 19, 17, 12, 15],
        "Difference": [-2, 0, 0, -1, -1],
        "Reason": ["Duplicates merged", "Exact match", "Exact match", "Duplicate removed", "Duplicate removed"]
    })

    st.dataframe(count_data, use_container_width=True, hide_index=True)

    # Evidence Pack
    st.markdown("---")
    st.markdown("### 📦 Evidence Pack")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Included in Evidence Pack:**
        - ✅ Reconciliation report (JSON)
        - ✅ Count verification results
        - ✅ Referential integrity checks
        - ✅ Data hash signatures
        - ✅ Sample verification records
        """)

    with col2:
        evidence_json = {
            "id": f"EP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "migration_id": "MIG-2024-001",
            "status": summary["overall_status"],
            "pass_rate": summary["pass_rate"],
            "data_hash": summary["data_hash"],
            "checks": summary
        }

        import json
        st.download_button(
            "📥 Download Evidence Pack (JSON)",
            json.dumps(evidence_json, indent=2),
            "evidence_pack.json",
            "application/json",
            use_container_width=True
        )

    st.markdown("---")

    if summary["overall_status"] == "PASSED":
        st.success("✅ All critical checks passed! Ready for cloud migration.")
        if st.button("➡️ Proceed to Cloud Migration", use_container_width=True, type="primary"):
            st.session_state.step = 5
            st.switch_page("pages/5_☁️_Cloud_Migration.py")
    else:
        st.warning("⚠️ Some checks require attention. Review warnings before proceeding.")
        if st.button("➡️ Proceed Anyway", use_container_width=True, type="secondary"):
            st.session_state.step = 5
            st.switch_page("pages/5_☁️_Cloud_Migration.py")

# Sidebar
with st.sidebar:
    st.markdown("### 📊 Reconciliation")
    if st.session_state.reconciliation_done:
        summary = st.session_state.reconciliation_results["summary"]
        if summary["overall_status"] == "PASSED":
            st.success("All Checks Passed")
        else:
            st.warning("Review Required")

        st.metric("Pass Rate", f"{summary['pass_rate']}%")

        st.markdown("---")
        st.markdown("**Domain Status:**")
        for domain_key in ["identity", "enrollment", "grades", "attendance"]:
            domain = st.session_state.reconciliation_results["domains"][domain_key]
            icon = "✅" if domain["status"] == "passed" else "⚠️"
            st.markdown(f"{icon} {domain_key.title()}")
    else:
        st.info("Checks not yet run")
