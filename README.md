# EduSync AI — School Data Migration Platform

A Streamlit-based platform for migrating and reconciling school operational data (enrollment, grades, attendance, transcripts) into a canonical format, with exports to OneRoster and Ed-Fi.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## What it does

Schools run on a tangle of student information systems, gradebooks, LMS exports, and attendance tools — each with its own schema. EduSync AI ingests those feeds and produces a clean, canonical, exchange-ready dataset.

- **Ingest** CSV/Excel feeds from multiple source systems
- **Resolve identities** across systems (students, staff, sections) to stable canonical IDs
- **Process** enrollment, grades & transcripts, and attendance into the canonical data model
- **Reconcile** counts, keys, and row-level differences between source and target
- **Export** to industry-standard formats (**OneRoster CSV** and **Ed-Fi** payloads)

## Built around the DMaaS Playbook

The pipeline is organized to match sections of the Data-Migration-as-a-Service playbook:

| Stage | Playbook section |
|---|---|
| Canonical Data Model | §4B |
| Identity Resolution | §1.1.1 |
| Enrollment Processing | §1.1.2 |
| Grades & Transcripts | §1.1.4 |
| Attendance | §1.1.5 |
| Reconciliation | §4E |
| OneRoster / Ed-Fi Export | §1A |

## Quick start

```bash
git clone https://github.com/Hassan-Naeem-code/Actus-project.git
cd Actus-project

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

streamlit run app.py
```

The app opens in your browser. Navigate through the sidebar pages to walk the pipeline end-to-end.

## Project layout

```
.
├── app.py                # Streamlit home + page config
├── pages/                # Streamlit multi-page entries
├── modules/              # Core processing logic (ingest, resolve, process)
├── models/               # Canonical data model classes
├── reconciliation/       # Cross-system reconciliation logic
├── exports/              # OneRoster + Ed-Fi export writers
├── requirements.txt
└── README.md
```

## Why this matters

K-12 districts waste weeks per onboarding because each vendor wants a slightly different schema. A single canonical pipeline with automated reconciliation turns that migration from a 6-week custom engagement into a reusable product.

## Status

Actively evolving. The core ingest → resolve → process → export flow works; reconciliation and Ed-Fi export tooling are being expanded.

## License

MIT
