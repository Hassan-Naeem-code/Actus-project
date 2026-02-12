"""
Step 5: Cloud Migration
Secure cloud upload simulation
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="Cloud Migration - EduSync AI",
    page_icon="☁️",
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
    .cloud-card {
        background: linear-gradient(135deg, #1e293b, #334155);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        border: 2px solid #475569;
        cursor: pointer;
        transition: all 0.3s;
    }
    .cloud-card:hover {
        border-color: #3b82f6;
    }
    .security-badge {
        background: #14532d;
        color: #bbf7d0;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin: 0.25rem;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Check prerequisites
if 'cleaned_students' not in st.session_state:
    st.warning("Please complete previous steps first.")
    if st.button("← Go to Reconciliation"):
        st.switch_page("pages/4_📊_Reconciliation.py")
    st.stop()

# Initialize state
if 'migration_done' not in st.session_state:
    st.session_state.migration_done = False

st.markdown('<span class="step-indicator">Step 5: Secure Cloud Migration</span>', unsafe_allow_html=True)

col_back, col_title = st.columns([1, 11])
with col_back:
    if st.button("⬅️ Back"):
        st.switch_page("pages/4_📊_Reconciliation.py")

if not st.session_state.migration_done:
    st.markdown("### ☁️ Select Cloud Destination")

    col1, col2, col3 = st.columns(3)

    with col1:
        aws_selected = st.button("", key="aws_btn", use_container_width=True)
        st.markdown("""
        <div class="cloud-card">
            <div style="font-size: 3rem;">☁️</div>
            <h3 style="color: #f8fafc; margin: 0.5rem 0;">Amazon Web Services</h3>
            <p style="color: #94a3b8; margin: 0;">S3 + RDS + Lambda</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        azure_selected = st.button("", key="azure_btn", use_container_width=True)
        st.markdown("""
        <div class="cloud-card">
            <div style="font-size: 3rem;">🔷</div>
            <h3 style="color: #f8fafc; margin: 0.5rem 0;">Microsoft Azure</h3>
            <p style="color: #94a3b8; margin: 0;">Blob + SQL + Functions</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        gcp_selected = st.button("", key="gcp_btn", use_container_width=True)
        st.markdown("""
        <div class="cloud-card">
            <div style="font-size: 3rem;">🌐</div>
            <h3 style="color: #f8fafc; margin: 0.5rem 0;">Google Cloud Platform</h3>
            <p style="color: #94a3b8; margin: 0;">GCS + Cloud SQL + Functions</p>
        </div>
        """, unsafe_allow_html=True)

    cloud_provider = st.selectbox(
        "Select Cloud Provider",
        ["Amazon Web Services (AWS)", "Microsoft Azure", "Google Cloud Platform (GCP)"]
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔒 Security Options")

        encryption = st.checkbox("End-to-end encryption (AES-256)", value=True)
        pii_masking = st.checkbox("Data masking for PII fields", value=True)
        backup = st.checkbox("Create backup before migration", value=True)
        audit_log = st.checkbox("Enable comprehensive audit logging", value=True)
        mfa = st.checkbox("Require MFA for access", value=True)

        st.markdown("### Security Certifications")
        st.markdown("""
        <div>
            <span class="security-badge">🔐 SOC 2 Type II</span>
            <span class="security-badge">📋 FERPA Compliant</span>
            <span class="security-badge">🛡️ COPPA Compliant</span>
            <span class="security-badge">🔒 HIPAA Ready</span>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 📋 Data to Migrate")

        records_count = len(st.session_state.cleaned_students)
        guardians_count = len(st.session_state.get('guardians_data', pd.DataFrame()))
        enrollments_count = len(st.session_state.get('enrollments_data', pd.DataFrame()))
        grades_count = len(st.session_state.get('grades_data', pd.DataFrame()))
        attendance_count = len(st.session_state.get('attendance_data', pd.DataFrame()))

        st.markdown(f"""
        | Entity | Records |
        |--------|---------|
        | Students | {records_count} |
        | Guardians | {guardians_count} |
        | Enrollments | {enrollments_count} |
        | Grades | {grades_count} |
        | Attendance | {attendance_count} |
        | **Total** | **{records_count + guardians_count + enrollments_count + grades_count + attendance_count}** |
        """)

        st.info("📌 Original source systems will NOT be modified.")

    st.markdown("---")

    st.markdown("""
    <div style="background: #1e293b; border-radius: 12px; padding: 1rem; border: 1px solid #334155;">
        <div style="background: #3b82f6; color: white; padding: 0.75rem 1rem; border-radius: 12px; display: inline-block;">
            🚀 Ready to securely migrate your unified data to <strong>{}</strong>.
            All data will be encrypted in transit and at rest.
        </div>
    </div>
    """.format(cloud_provider), unsafe_allow_html=True)

    if st.button("🚀 Start Secure Migration", use_container_width=True, type="primary"):
        progress = st.progress(0)
        status = st.empty()
        detail = st.empty()

        migration_steps = [
            ("Establishing secure connection...", 5, "Initializing TLS 1.3"),
            ("Authenticating with cloud provider...", 10, "OAuth 2.0 token exchange"),
            ("Creating encrypted tunnel (AES-256)...", 15, "End-to-end encryption active"),
            ("Preparing data packages...", 20, "Chunking data for transfer"),
            ("Uploading Students (1/5)...", 30, f"{records_count} records"),
            ("Uploading Guardians (2/5)...", 40, f"{guardians_count} records"),
            ("Uploading Enrollments (3/5)...", 50, f"{enrollments_count} records"),
            ("Uploading Grades (4/5)...", 60, f"{grades_count} records"),
            ("Uploading Attendance (5/5)...", 70, f"{attendance_count} records"),
            ("Verifying data integrity (SHA-256)...", 80, "Hash verification in progress"),
            ("Creating database indexes...", 85, "Optimizing query performance"),
            ("Setting up access controls...", 90, "Role-based permissions"),
            ("Generating audit trail...", 95, "Compliance logging"),
            ("Migration complete!", 100, "All data transferred successfully")
        ]

        for step_text, prog, detail_text in migration_steps:
            status.markdown(f"**{step_text}**")
            detail.markdown(f"*{detail_text}*")
            progress.progress(prog)
            time.sleep(0.3)

        st.session_state.migration_done = True
        st.session_state.cloud_provider = cloud_provider
        st.session_state.migration_timestamp = datetime.now().isoformat()
        st.rerun()

else:
    st.success("✅ Migration completed successfully!")

    st.markdown("### 📊 Migration Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Status", "Success ✅")
    with col2:
        total_records = (
            len(st.session_state.cleaned_students) +
            len(st.session_state.get('guardians_data', pd.DataFrame())) +
            len(st.session_state.get('enrollments_data', pd.DataFrame())) +
            len(st.session_state.get('grades_data', pd.DataFrame())) +
            len(st.session_state.get('attendance_data', pd.DataFrame()))
        )
        st.metric("Records Migrated", f"{total_records:,}")
    with col3:
        st.metric("Transfer Time", "12.3s")
    with col4:
        st.metric("Data Integrity", "Verified ✓")

    st.markdown("---")

    st.markdown("### 🔒 Security Verification")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Encryption:**
        - ✅ AES-256 encryption at rest
        - ✅ TLS 1.3 encryption in transit
        - ✅ Key rotation enabled
        - ✅ PII fields masked
        """)

    with col2:
        st.markdown("""
        **Compliance:**
        - ✅ FERPA compliance verified
        - ✅ Audit trail generated
        - ✅ Access controls configured
        - ✅ Backup created
        """)

    st.markdown("---")

    st.markdown("### 📍 Cloud Endpoints")

    provider = st.session_state.get('cloud_provider', 'AWS')

    if "AWS" in provider:
        endpoints = {
            "API Gateway": "https://api.edusync.aws.example.com/v1",
            "S3 Bucket": "s3://edusync-migration-2024/",
            "RDS Instance": "edusync-prod.xxxxx.us-east-1.rds.amazonaws.com"
        }
    elif "Azure" in provider:
        endpoints = {
            "API Management": "https://edusync.azure-api.net/v1",
            "Blob Storage": "https://edusyncstorage.blob.core.windows.net/",
            "SQL Database": "edusync-prod.database.windows.net"
        }
    else:
        endpoints = {
            "Cloud Endpoints": "https://edusync-api.endpoints.project.cloud.goog",
            "Cloud Storage": "gs://edusync-migration-2024/",
            "Cloud SQL": "edusync-prod:us-central1:edusync-db"
        }

    for name, endpoint in endpoints.items():
        st.code(f"{name}: {endpoint}")

    st.markdown("---")

    if st.button("➡️ Proceed to Export Options", use_container_width=True, type="primary"):
        st.session_state.step = 6
        st.switch_page("pages/6_📤_Export_Data.py")

# Sidebar
with st.sidebar:
    st.markdown("### ☁️ Migration Status")
    if st.session_state.migration_done:
        st.success("Migration Complete")
        st.markdown(f"**Provider:** {st.session_state.get('cloud_provider', 'AWS')}")
        st.markdown(f"**Time:** {st.session_state.get('migration_timestamp', '')[:19]}")
    else:
        st.info("Migration pending")

    st.markdown("---")
    st.markdown("### Security Features")
    st.markdown("""
    - 🔐 AES-256 Encryption
    - 🔒 TLS 1.3 Transport
    - 📋 Audit Logging
    - 🛡️ FERPA Compliant
    """)
