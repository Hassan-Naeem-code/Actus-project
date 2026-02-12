"""
Step 6: Export Data
OneRoster and Ed-Fi export options
"""

import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exports.oneroster import OneRosterExporter
from exports.edfi import EdFiExporter

st.set_page_config(
    page_title="Export Data - EduSync AI",
    page_icon="📤",
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
    .export-card {
        background: linear-gradient(135deg, #1e293b, #334155);
        border-radius: 12px;
        padding: 1.5rem;
        border: 2px solid #475569;
        margin: 0.5rem 0;
    }
    .file-item {
        background: #1e293b;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        margin: 0.25rem 0;
        border-left: 3px solid #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

# Check prerequisites
if 'cleaned_students' not in st.session_state:
    st.warning("Please complete previous steps first.")
    if st.button("← Go to Cloud Migration"):
        st.switch_page("pages/5_☁️_Cloud_Migration.py")
    st.stop()

st.markdown('<span class="step-indicator">Step 6: Export Data</span>', unsafe_allow_html=True)

col_back, col_title = st.columns([1, 11])
with col_back:
    if st.button("⬅️ Back"):
        st.switch_page("pages/5_☁️_Cloud_Migration.py")

st.markdown("### 📤 Data Export Options")
st.markdown("*Export your migrated data to industry-standard formats for LMS and state reporting integration*")

# Tabs for different export types
tab1, tab2, tab3 = st.tabs(["📋 OneRoster Export", "🏛️ Ed-Fi Export", "📦 Custom Export"])

with tab1:
    st.markdown("""
    <div class="export-card">
        <h3 style="color: #f8fafc; margin: 0;">📋 OneRoster 1.2 Export</h3>
        <p style="color: #94a3b8; margin: 0.5rem 0;">
            Industry standard for SIS-to-LMS data exchange. Compatible with Canvas, Blackboard, Schoology, and more.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Files Included:")

    files = [
        ("users.csv", "Students, teachers, and guardians"),
        ("orgs.csv", "Schools and districts"),
        ("courses.csv", "Course catalog"),
        ("classes.csv", "Class sections"),
        ("enrollments.csv", "Roster memberships"),
        ("academicSessions.csv", "Terms and school years"),
    ]

    for filename, description in files:
        st.markdown(f"""
        <div class="file-item">
            📄 <strong>{filename}</strong> - {description}
        </div>
        """, unsafe_allow_html=True)

    if st.button("📥 Generate OneRoster Package", use_container_width=True, type="primary", key="oneroster_gen"):
        with st.spinner("Generating OneRoster files..."):
            # Create exporter and populate with data
            exporter = OneRosterExporter()

            # Add organization
            exporter.add_organization({
                "id": "SCH001",
                "name": "Lincoln High School",
                "type": "school"
            })

            # Add academic session
            exporter.add_academic_session({
                "id": "2023-2024",
                "name": "2023-2024 School Year",
                "type": "schoolYear",
                "start_date": "2023-08-15",
                "end_date": "2024-05-25",
                "school_year": "2023-2024"
            })

            # Add students
            for _, row in st.session_state.cleaned_students.iterrows():
                exporter.add_student(row.to_dict(), "SCH001")

            # Add guardians if available
            if 'guardians_data' in st.session_state:
                for _, row in st.session_state.guardians_data.iterrows():
                    exporter.add_guardian(row.to_dict(), "SCH001")

            # Generate all files
            all_files = exporter.export_all()

            time.sleep(1)

        st.success("✅ OneRoster package generated!")

        # Show stats
        stats = exporter.get_stats()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Students", stats["students"])
        with col2:
            st.metric("Guardians", stats["guardians"])
        with col3:
            st.metric("Organizations", stats["organizations"])
        with col4:
            st.metric("Total Users", stats["users"])

        # Download buttons
        st.markdown("#### Download Files:")

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "📥 Download users.csv",
                all_files["users.csv"],
                "users.csv",
                "text/csv",
                use_container_width=True
            )
            st.download_button(
                "📥 Download orgs.csv",
                all_files["orgs.csv"],
                "orgs.csv",
                "text/csv",
                use_container_width=True
            )
            st.download_button(
                "📥 Download courses.csv",
                all_files["courses.csv"],
                "courses.csv",
                "text/csv",
                use_container_width=True
            )

        with col2:
            st.download_button(
                "📥 Download classes.csv",
                all_files["classes.csv"],
                "classes.csv",
                "text/csv",
                use_container_width=True
            )
            st.download_button(
                "📥 Download enrollments.csv",
                all_files["enrollments.csv"],
                "enrollments.csv",
                "text/csv",
                use_container_width=True
            )
            st.download_button(
                "📥 Download academicSessions.csv",
                all_files["academicSessions.csv"],
                "academicSessions.csv",
                "text/csv",
                use_container_width=True
            )

        # Manifest
        manifest = exporter.get_manifest()
        st.download_button(
            "📥 Download manifest.csv",
            "\n".join([f"{k},{v}" for k, v in manifest.items()]),
            "manifest.csv",
            "text/csv",
            use_container_width=True
        )

with tab2:
    st.markdown("""
    <div class="export-card">
        <h3 style="color: #f8fafc; margin: 0;">🏛️ Ed-Fi Data Standard Export</h3>
        <p style="color: #94a3b8; margin: 0.5rem 0;">
            State education agency reporting format. Used for compliance reporting and data exchange with SEAs.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Files Included:")

    edfi_files = [
        ("students.json", "Student demographic records"),
        ("studentSchoolAssociations.json", "Enrollment records"),
        ("staff.json", "Staff/teacher records"),
        ("courses.json", "Course catalog"),
        ("grades.json", "Student grades"),
        ("studentSchoolAttendanceEvents.json", "Attendance events"),
    ]

    for filename, description in edfi_files:
        st.markdown(f"""
        <div class="file-item">
            📄 <strong>{filename}</strong> - {description}
        </div>
        """, unsafe_allow_html=True)

    if st.button("📥 Generate Ed-Fi Package", use_container_width=True, type="primary", key="edfi_gen"):
        with st.spinner("Generating Ed-Fi JSON files..."):
            # Create exporter
            exporter = EdFiExporter(school_id="255901001", school_year=2024)

            # Add students
            for _, row in st.session_state.cleaned_students.iterrows():
                exporter.add_student(row.to_dict())

            # Add grades if available
            if 'grades_data' in st.session_state:
                for _, row in st.session_state.grades_data.iterrows():
                    exporter.add_grade(row.to_dict())

            # Add attendance if available
            if 'attendance_data' in st.session_state:
                for _, row in st.session_state.attendance_data.iterrows():
                    exporter.add_attendance_event(row.to_dict())

            # Generate combined export
            combined_json = exporter.export_combined_json()

            time.sleep(1)

        st.success("✅ Ed-Fi package generated!")

        # Show stats
        stats = exporter.get_stats()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Students", stats["students"])
        with col2:
            st.metric("Enrollments", stats["student_school_associations"])
        with col3:
            st.metric("Grades", stats["grades"])
        with col4:
            st.metric("Attendance", stats["attendance_events"])

        # Download buttons
        st.markdown("#### Download Files:")

        all_files = exporter.export_all()

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "📥 Download students.json",
                all_files["students.json"],
                "students.json",
                "application/json",
                use_container_width=True
            )
            st.download_button(
                "📥 Download enrollments.json",
                all_files["studentSchoolAssociations.json"],
                "studentSchoolAssociations.json",
                "application/json",
                use_container_width=True
            )
            st.download_button(
                "📥 Download grades.json",
                all_files["grades.json"],
                "grades.json",
                "application/json",
                use_container_width=True
            )

        with col2:
            st.download_button(
                "📥 Download staff.json",
                all_files["staff.json"],
                "staff.json",
                "application/json",
                use_container_width=True
            )
            st.download_button(
                "📥 Download courses.json",
                all_files["courses.json"],
                "courses.json",
                "application/json",
                use_container_width=True
            )
            st.download_button(
                "📥 Download attendance.json",
                all_files["studentSchoolAttendanceEvents.json"],
                "studentSchoolAttendanceEvents.json",
                "application/json",
                use_container_width=True
            )

        # Combined file
        st.download_button(
            "📥 Download Combined Ed-Fi Bundle",
            combined_json,
            "edfi_bundle.json",
            "application/json",
            use_container_width=True
        )

with tab3:
    st.markdown("""
    <div class="export-card">
        <h3 style="color: #f8fafc; margin: 0;">📦 Custom Export</h3>
        <p style="color: #94a3b8; margin: 0.5rem 0;">
            Download cleaned data in various formats for custom integrations.
        </p>
    </div>
    """, unsafe_allow_html=True)

    export_format = st.selectbox("Select Format", ["CSV", "JSON", "Excel"])

    entities = st.multiselect(
        "Select Entities to Export",
        ["Students", "Guardians", "Enrollments", "Grades", "Attendance"],
        default=["Students"]
    )

    if st.button("📥 Generate Custom Export", use_container_width=True, type="primary", key="custom_gen"):
        with st.spinner("Generating export..."):
            exports = {}

            if "Students" in entities:
                df = st.session_state.cleaned_students
                if export_format == "CSV":
                    exports["students"] = df.to_csv(index=False)
                elif export_format == "JSON":
                    exports["students"] = df.to_json(orient="records", indent=2)

            if "Guardians" in entities and 'guardians_data' in st.session_state:
                df = st.session_state.guardians_data
                if export_format == "CSV":
                    exports["guardians"] = df.to_csv(index=False)
                elif export_format == "JSON":
                    exports["guardians"] = df.to_json(orient="records", indent=2)

            if "Enrollments" in entities and 'enrollments_data' in st.session_state:
                df = st.session_state.enrollments_data
                if export_format == "CSV":
                    exports["enrollments"] = df.to_csv(index=False)
                elif export_format == "JSON":
                    exports["enrollments"] = df.to_json(orient="records", indent=2)

            if "Grades" in entities and 'grades_data' in st.session_state:
                df = st.session_state.grades_data
                if export_format == "CSV":
                    exports["grades"] = df.to_csv(index=False)
                elif export_format == "JSON":
                    exports["grades"] = df.to_json(orient="records", indent=2)

            if "Attendance" in entities and 'attendance_data' in st.session_state:
                df = st.session_state.attendance_data
                if export_format == "CSV":
                    exports["attendance"] = df.to_csv(index=False)
                elif export_format == "JSON":
                    exports["attendance"] = df.to_json(orient="records", indent=2)

            time.sleep(0.5)

        st.success(f"✅ Generated {len(exports)} file(s)!")

        for name, content in exports.items():
            ext = "csv" if export_format == "CSV" else "json"
            mime = "text/csv" if export_format == "CSV" else "application/json"
            st.download_button(
                f"📥 Download {name}.{ext}",
                content,
                f"{name}.{ext}",
                mime,
                use_container_width=True,
                key=f"dl_{name}"
            )

st.markdown("---")

if st.button("➡️ Proceed to Summary", use_container_width=True, type="primary"):
    st.session_state.step = 7
    st.switch_page("pages/7_✅_Complete.py")

# Sidebar
with st.sidebar:
    st.markdown("### 📤 Export Options")

    st.markdown("""
    **OneRoster 1.2**
    - LMS Integration
    - Canvas, Blackboard, etc.

    **Ed-Fi**
    - State Reporting
    - SEA Compliance

    **Custom**
    - CSV, JSON, Excel
    - API Integration
    """)

    st.markdown("---")
    st.markdown("### Quick Links")
    st.markdown("[OneRoster Spec](https://www.imsglobal.org/oneroster)")
    st.markdown("[Ed-Fi Docs](https://www.ed-fi.org/)")
