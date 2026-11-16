"""Streamlit Web App: Student Grade & Report Card Generator."""

from __future__ import annotations

import csv
import html
import io
from contextlib import nullcontext
from datetime import date
from typing import Any

import streamlit as st

from auth import (
    CORE_SUBJECTS,
    DEFAULT_SCHOOL,
    DEMO_STUDENT_USERNAMES,
    ELECTIVE_OPTIONS,
    ROLE_ADMIN,
    ROLE_STUDENT,
    ROLE_TEACHER,
    VALID_ROLES,
    UserAccount,
    authenticate_user,
    build_empty_student_subjects,
    delete_user_account,
    generate_random_demo_assignments,
    get_default_student_roster,
    get_default_users,
    get_student_subject_names,
    register_user,
)
from grading import (
    SCALE_PLUS_MINUS,
    SCALE_STANDARD,
    ReportCardSummary,
    SubjectInput,
    calculate_report_card,
    export_report_card_csv,
    export_report_card_html,
    get_grade_tier_colors,
    get_honor_standing,
    get_letter_grade_and_gpa,
    validate_subjects,
)

st.set_page_config(
    page_title="Student Grade & Report Card Generator",
    page_icon="🎓",
    layout="wide",
)

CUSTOM_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }

  .block-container {
    max-width: 1180px !important;
    padding-top: 2rem !important;
    padding-bottom: 4rem !important;
  }

  /* Hero Header Banner */
  .hero-banner {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 55%, #312e81 100%);
    border-radius: 20px;
    padding: 32px 36px;
    color: #ffffff;
    box-shadow: 0 20px 40px -15px rgba(15, 23, 42, 0.25);
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.12);
  }
  .hero-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 20px;
    flex-wrap: wrap;
  }
  .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.14);
    border: 1px solid rgba(255, 255, 255, 0.22);
    color: #e0e7ff;
    font-size: 0.76rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 5px 13px;
    border-radius: 999px;
    margin-bottom: 12px;
  }
  .main-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 2.15rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.025em;
    margin: 0 0 8px 0;
    line-height: 1.2;
  }
  .sub-title {
    font-size: 1rem;
    color: #cbd5e1;
    max-width: 680px;
    line-height: 1.55;
    margin: 0;
  }
  .hero-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 20px;
    padding-top: 18px;
    border-top: 1px solid rgba(255, 255, 255, 0.14);
  }
  .hero-pill {
    background: rgba(15, 23, 42, 0.45);
    border: 1px solid rgba(255, 255, 255, 0.16);
    color: #f8fafc;
    border-radius: 10px;
    padding: 7px 14px;
    font-size: 0.82rem;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .hero-pill span {
    color: #93c5fd;
    font-weight: 700;
  }

  /* Login & User Profile Cards */
  .auth-card-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.22rem;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 4px 0;
  }
  .auth-card-sub {
    font-size: 0.86rem;
    color: #64748b;
    margin: 0 0 16px 0;
  }
  .demo-creds-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #2563eb;
    border-radius: 10px;
    padding: 12px 15px;
    font-size: 0.82rem;
    color: #334155;
    margin-top: 12px;
    line-height: 1.6;
  }
  .Demo-code {
    background: #e2e8f0;
    color: #0f172a;
    padding: 1px 6px;
    border-radius: 5px;
    font-family: monospace;
    font-weight: 700;
  }
  .user-profile-box {
    background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
    border: 1px solid #bfdbfe;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 12px;
    color: #0f172a;
  }
  .user-profile-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 6px;
  }
  .user-profile-name {
    font-weight: 800;
    font-size: 0.95rem;
    color: #0f172a;
  }
  .role-badge-student {
    background: #dbeafe;
    color: #1e40af;
    font-size: 0.7rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 2px 8px;
    border-radius: 999px;
  }
  .role-badge-instructor {
    background: #ede9fe;
    color: #5b21b6;
    font-size: 0.7rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 2px 8px;
    border-radius: 999px;
  }
  .role-badge-admin {
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #fcd34d;
    font-size: 0.7rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 2px 8px;
    border-radius: 999px;
  }
  .user-profile-meta {
    font-size: 0.78rem;
    color: #475569;
    font-weight: 500;
  }

  /* Section Header Cards */
  .section-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    margin: 8px 0 14px 0;
  }
  .section-title-wrap {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .step-pill {
    background: linear-gradient(135deg, #1e3a8a, #2563eb);
    color: #ffffff;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 5px 11px;
    border-radius: 8px;
  }
  .section-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.25rem;
    font-weight: 800;
    color: #0f172a;
    margin: 0;
  }
  .section-sub {
    font-size: 0.85rem;
    color: #64748b;
    font-weight: 500;
  }

  /* Bordered Container Card Styling */
  [data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff;
    border-radius: 16px !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 4px 20px -4px rgba(15, 23, 42, 0.05) !important;
    padding: 8px !important;
  }

  /* Live Inline Subject Preview Pill */
  .live-preview-pill {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    height: 38px;
    padding: 0 12px;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 700;
    border: 1px solid transparent;
    white-space: nowrap;
  }

  /* Sidebar Scale Reference Table */
  .scale-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
    background: #ffffff;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
  }
  .scale-table th {
    background: #f1f5f9;
    color: #475569;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 8px 10px;
    text-align: left;
    border-bottom: 1px solid #e2e8f0;
  }
  .scale-table td {
    padding: 7px 10px;
    border-bottom: 1px solid #f1f5f9;
    color: #1e293b;
    font-weight: 500;
  }
  .scale-chip {
    display: inline-block;
    min-width: 30px;
    text-align: center;
    padding: 2px 7px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 0.76rem;
  }

  /* Official Report Card Showcase */
  .report-card-box {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 20px 45px -15px rgba(15, 23, 42, 0.12);
    margin-top: 10px;
    color: #0f172a;
  }
  .rc-top-accent {
    height: 8px;
    background: linear-gradient(90deg, #1e3a8a 0%, #2563eb 50%, #4f46e5 100%);
  }
  .rc-body {
    padding: 32px 36px;
  }
  .rc-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 16px;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 20px;
    margin-bottom: 22px;
  }
  .rc-brand {
    display: flex;
    align-items: center;
    gap: 14px;
  }
  .rc-crest {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    background: linear-gradient(135deg, #1e3a8a, #3b82f6);
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.65rem;
    box-shadow: 0 8px 16px -4px rgba(37, 99, 235, 0.35);
    flex-shrink: 0;
  }
  .rc-school {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.55rem;
    font-weight: 800;
    color: #0f172a;
    margin: 0 !important;
    letter-spacing: -0.02em;
    line-height: 1.25;
  }
  .rc-sub {
    font-size: 0.88rem;
    color: #64748b;
    margin: 3px 0 0 0 !important;
    font-weight: 500;
  }
  .rc-badge-group {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 6px;
  }
  .status-banner-pass {
    background: #ecfdf5;
    color: #065f46;
    border: 1.5px solid #6ee7b7;
    padding: 8px 20px;
    border-radius: 999px;
    font-weight: 800;
    font-size: 0.9rem;
    letter-spacing: 0.04em;
  }
  .status-banner-fail {
    background: #fef2f2;
    color: #991b1b;
    border: 1.5px solid #fca5a5;
    padding: 8px 20px;
    border-radius: 999px;
    font-weight: 800;
    font-size: 0.9rem;
    letter-spacing: 0.04em;
  }
  .honor-pill {
    background: #f1f5f9;
    color: #334155;
    border: 1px solid #cbd5e1;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 700;
  }
  .rc-meta {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 14px 20px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 24px;
  }
  .rc-meta-item {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .rc-meta-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #64748b;
    font-weight: 700;
  }
  .rc-meta-val {
    font-size: 0.96rem;
    font-weight: 700;
    color: #0f172a;
  }
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(195px, 1fr));
    gap: 16px;
    margin-bottom: 26px;
  }
  .kpi-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 18px 16px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
    position: relative;
    overflow: hidden;
  }
  .kpi-card-top {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
  }
  .kpi-label {
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #64748b;
    font-weight: 700;
    margin-bottom: 8px;
  }
  .kpi-value {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.85rem;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.15;
  }
  .kpi-sub {
    font-size: 0.78rem;
    color: #64748b;
    margin-top: 6px;
    font-weight: 600;
  }
  .rc-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    margin-bottom: 24px;
    font-size: 0.92rem;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    overflow: hidden;
  }
  .rc-table th {
    background: #0f172a;
    color: #f8fafc;
    padding: 12px 15px;
    text-align: left;
    font-weight: 700;
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border: none;
  }
  .rc-table td {
    padding: 12px 15px;
    border-bottom: 1px solid #e2e8f0;
    color: #1e293b;
    vertical-align: middle;
  }
  .rc-table tbody tr:nth-child(even) {
    background: #f8fafc;
  }
  .rc-table tbody tr:hover {
    background: #f1f5f9;
  }
  .rc-table tfoot td {
    background: #f1f5f9;
    font-weight: 800;
    color: #0f172a;
    border-top: 2px solid #cbd5e1;
    border-bottom: none;
  }
  .rc-num { text-align: right !important; }
  .rc-center { text-align: center !important; }
  .pct-bar-wrap {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 5px;
    min-width: 120px;
  }
  .pct-bar-track {
    width: 100%;
    height: 6px;
    background: #e2e8f0;
    border-radius: 999px;
    overflow: hidden;
  }
  .pct-bar-fill {
    height: 100%;
    border-radius: 999px;
  }
  .grade-badge {
    display: inline-block;
    min-width: 36px;
    padding: 3px 10px;
    border-radius: 8px;
    font-weight: 800;
    font-size: 0.84rem;
    text-align: center;
  }
  .pill-pass {
    background: #dcfce7;
    color: #166534;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.03em;
    display: inline-block;
  }
  .pill-fail {
    background: #fee2e2;
    color: #991b1b;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.03em;
    display: inline-block;
  }
  .rc-remarks {
    border: 1px solid #bfdbfe;
    border-left: 5px solid #2563eb;
    background: #eff6ff;
    padding: 16px 20px;
    border-radius: 10px;
    font-size: 0.92rem;
    line-height: 1.65;
    color: #1e293b;
  }

  /* Visual Analytics Chart Card */
  .analytics-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 24px 28px;
    margin-top: 20px;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
    color: #0f172a;
  }
  .analytics-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 18px;
    padding-bottom: 12px;
    border-bottom: 1px solid #f1f5f9;
  }
  .analytics-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.08rem;
    font-weight: 800;
    color: #0f172a;
    margin: 0;
  }
  .analytics-legend {
    font-size: 0.8rem;
    color: #64748b;
    font-weight: 600;
  }
  .chart-row {
    display: grid;
    grid-template-columns: 180px 1fr 95px;
    align-items: center;
    gap: 14px;
    margin-bottom: 12px;
  }
  .chart-subj {
    font-size: 0.88rem;
    font-weight: 700;
    color: #1e293b;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .chart-track {
    position: relative;
    height: 14px;
    background: #f1f5f9;
    border-radius: 999px;
    overflow: visible;
  }
  .chart-fill {
    height: 100%;
    border-radius: 999px;
  }
  .chart-cutoff {
    position: absolute;
    top: -4px;
    bottom: -4px;
    width: 2px;
    background: #dc2626;
    z-index: 2;
  }
  .chart-val {
    text-align: right;
    font-size: 0.84rem;
    font-weight: 700;
    color: #0f172a;
  }
</style>
"""


DEFAULT_SUBJECTS: list[dict[str, object]] = [
    {"id": 1, "name": "History", "marks": 84.0, "max_marks": 100.0, "credits": 1.0},
    {"id": 2, "name": "Science", "marks": 88.0, "max_marks": 100.0, "credits": 1.0},
    {"id": 3, "name": "Math", "marks": 92.0, "max_marks": 100.0, "credits": 1.0},
    {"id": 4, "name": "English", "marks": 86.0, "max_marks": 100.0, "credits": 1.0},
    {"id": 5, "name": "Computer Science", "marks": 95.0, "max_marks": 100.0, "credits": 1.0},
    {"id": 6, "name": "Art & Design", "marks": 90.0, "max_marks": 100.0, "credits": 1.0},
]


def _card_container() -> Any:
    """Return a bordered Streamlit container when available, or a no-op context."""
    container_fn = getattr(st, "container", None)
    if callable(container_fn):
        try:
            return container_fn(border=True)
        except TypeError:
            return container_fn()
    return nullcontext()


def _init_state() -> None:
    """Initialize Streamlit session state variables."""
    if "users" not in st.session_state:
        st.session_state.users = get_default_users()
    if "roster" not in st.session_state:
        st.session_state.roster = get_default_student_roster()
    if "active_student_id" not in st.session_state:
        st.session_state.active_student_id = "STU-2026-104"
    if "school_policy" not in st.session_state:
        st.session_state.school_policy = {
            "school_name": "Westview Academy of Arts & Sciences",
            "term": "Fall Semester 2026",
            "passing_percentage": 60,
            "scale": SCALE_PLUS_MINUS,
            "require_all_subjects_pass": True,
            "use_credit_weights": False,
            "grade_curve_bonus": 0.0,
        }
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "subjects" not in st.session_state:
        st.session_state.subjects = [dict(row) for row in DEFAULT_SUBJECTS]
    if "next_id" not in st.session_state:
        st.session_state.next_id = len(DEFAULT_SUBJECTS) + 1
    if "show_report" not in st.session_state:
        st.session_state.show_report = True
    if "active_page" not in st.session_state:
        st.session_state.active_page = "marks"
    if "drop_lowest_grade" not in st.session_state:
        st.session_state.drop_lowest_grade = False


def _load_student_from_roster(student_id: str) -> None:
    """Load a student's course marks from the class roster into the active editor."""
    st.session_state.active_student_id = student_id
    record = st.session_state.roster.get(student_id)
    if record and isinstance(record.get("subjects"), list):
        rows = [dict(r) for r in record["subjects"]]  # type: ignore[index]
        st.session_state.subjects = rows
        st.session_state.next_id = max((int(r["id"]) for r in rows), default=0) + 1
    st.session_state.drop_lowest_grade = False
    st.session_state.show_report = True


def _login_as(account: UserAccount) -> None:
    """Set the active authenticated user session and load matching student record."""
    st.session_state.current_user = account
    if account.role == ROLE_STUDENT and account.student_id in st.session_state.roster:
        if account.username in DEMO_STUDENT_USERNAMES:
            rec_electives = st.session_state.roster[account.student_id].get(
                "electives", list(account.electives)
            )
            e_pair = (
                (str(rec_electives[0]), str(rec_electives[1]))
                if isinstance(rec_electives, (list, tuple)) and len(rec_electives) >= 2
                else account.electives
            )
            st.session_state.roster[account.student_id]["subjects"] = (
                generate_random_demo_assignments(6, e_pair)
            )
        _load_student_from_roster(account.student_id)
    else:
        _load_student_from_roster(st.session_state.active_student_id)
    st.session_state.drop_lowest_grade = False
    st.session_state.active_page = "marks"
    st.session_state.show_report = True


def _logout_user() -> None:
    """Clear the active authenticated user session."""
    st.session_state.current_user = None


def _add_subject_row(
    name: str = "",
    marks: float = 0.0,
    max_marks: float = 100.0,
    credits: float = 1.0,
) -> None:
    row_id = st.session_state.next_id
    st.session_state.next_id += 1
    st.session_state.subjects.append(
        {
            "id": row_id,
            "name": name,
            "marks": marks,
            "max_marks": max_marks,
            "credits": credits,
        }
    )


def _remove_subject_row(row_id: int) -> None:
    st.session_state.subjects = [
        row for row in st.session_state.subjects if row["id"] != row_id
    ]


def _reset_sample_subjects() -> None:
    st.session_state.subjects = [dict(row) for row in DEFAULT_SUBJECTS]
    st.session_state.next_id = len(DEFAULT_SUBJECTS) + 1
    st.session_state.show_report = True


def _clear_all_marks() -> None:
    for row in st.session_state.subjects:
        row["marks"] = 0.0
    st.session_state.show_report = False


def _parse_uploaded_csv(file_text: str) -> list[dict[str, object]]:
    """Parse an uploaded CSV file with subject marks."""
    reader = csv.DictReader(io.StringIO(file_text))
    parsed: list[dict[str, object]] = []
    next_id = 1000
    for raw in reader:
        normalized = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
        name = (
            normalized.get("subject")
            or normalized.get("subject name")
            or normalized.get("name")
            or ""
        )
        marks_str = (
            normalized.get("marks")
            or normalized.get("marks obtained")
            or normalized.get("score")
            or "0"
        )
        max_str = (
            normalized.get("max marks")
            or normalized.get("max_marks")
            or normalized.get("total")
            or "100"
        )
        credits_str = normalized.get("credits") or normalized.get("weight") or "1"
        if not name:
            continue
        parsed.append(
            {
                "id": next_id,
                "name": name,
                "marks": float(marks_str),
                "max_marks": float(max_str),
                "credits": float(credits_str),
            }
        )
        next_id += 1
    return parsed


def _render_sidebar_scale_html(scale: str, passing_percentage: int) -> str:
    """Render a styled grade scale reference table for the sidebar."""
    if scale == SCALE_PLUS_MINUS:
        tiers = [
            ("A+", "97 – 100%", "4.0"),
            ("A", "93 – 96.9%", "4.0"),
            ("A-", "90 – 92.9%", "3.7"),
            ("B+", "87 – 89.9%", "3.3"),
            ("B", "83 – 86.9%", "3.0"),
            ("B-", "80 – 82.9%", "2.7"),
            ("C+", "77 – 79.9%", "2.3"),
            ("C", "73 – 76.9%", "2.0"),
            ("C-", "70 – 72.9%", "1.7"),
            ("D+ / D", f"{passing_percentage} – 69.9%", "1.3 / 1.0"),
            ("F", f"< {passing_percentage}%", "0.0"),
        ]
    else:
        tiers = [
            ("A", "90 – 100%", "4.0"),
            ("B", "80 – 89.9%", "3.0"),
            ("C", "70 – 79.9%", "2.0"),
            ("D", f"{passing_percentage} – 69.9%", "1.0"),
            ("F", f"< {passing_percentage}%", "0.0"),
        ]

    rows = []
    for letter, rng, gpa in tiers:
        bg, fg, _ = get_grade_tier_colors(letter)
        rows.append(
            f"<tr>"
            f"<td><span class='scale-chip' style='background:{bg};color:{fg};'>{html.escape(letter)}</span></td>"
            f"<td>{html.escape(rng)}</td>"
            f"<td style='text-align:right;font-weight:700;'>{html.escape(gpa)}</td>"
            f"</tr>"
        )
    return (
        "<table class='scale-table'>"
        "<thead><tr><th>Grade</th><th>Score Range</th><th style='text-align:right;'>GPA</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )


def _render_user_profile_html(user: UserAccount) -> str:
    """Render the signed-in user badge inside the sidebar."""
    if user.role == ROLE_ADMIN:
        role_cls = "role-badge-admin"
        icon = "🛡️"
    elif user.role == ROLE_TEACHER:
        role_cls = "role-badge-instructor"
        icon = "👩‍🏫"
    else:
        role_cls = "role-badge-student"
        icon = "🎓"
    return (
        f"<div class='user-profile-box'>"
        f"<div class='user-profile-top'>"
        f"<span class='user-profile-name'>{icon} {html.escape(user.full_name)}</span>"
        f"<span class='{role_cls}'>{html.escape(user.role)}</span>"
        f"</div>"
        f"<div class='user-profile-meta'>"
        f"ID: <strong>{html.escape(user.student_id)}</strong> &bull; {html.escape(user.grade_level)}<br>"
        f"🏫 {html.escape(user.school_name)}"
        f"</div>"
        f"</div>"
    )


def _render_live_row_badge(
    marks: float,
    max_marks: float,
    passing_percentage: float,
    scale: str,
) -> str:
    """Render a compact live grade pill for a single subject input row."""
    if max_marks <= 0 or marks < 0 or marks > max_marks:
        return (
            "<div class='live-preview-pill' style='background:#fef2f2;color:#b91c1c;border-color:#fecaca;'>"
            "⚠️ Invalid"
            "</div>"
        )
    pct = round((marks / max_marks) * 100.0, 1)
    letter, _ = get_letter_grade_and_gpa(pct, passing_percentage=passing_percentage, scale=scale)
    bg, fg, _ = get_grade_tier_colors(letter)
    return (
        f"<div class='live-preview-pill' style='background:{bg};color:{fg};'>"
        f"<span>{pct:.1f}%</span> &bull; <strong>{html.escape(letter)}</strong>"
        f"</div>"
    )


def _render_report_card_html(summary: ReportCardSummary, today_str: str) -> str:
    """Build the styled visual report card HTML block for Streamlit."""
    banner_cls = "status-banner-pass" if summary.passed else "status-banner-fail"
    banner_icon = "✓" if summary.passed else "✕"
    banner_label = "PASSED" if summary.passed else "FAILED"
    status_color = "#047857" if summary.passed else "#b91c1c"
    status_bar = "#10b981" if summary.passed else "#ef4444"
    standing_label = get_honor_standing(summary.gpa, summary.passed)
    overall_bg, overall_fg, overall_bar = get_grade_tier_colors(summary.overall_letter_grade)

    rows = []
    for subj in summary.subjects:
        pill_cls = "pill-pass" if subj.passed else "pill-fail"
        pill_icon = "✓" if subj.passed else "✕"
        g_bg, g_fg, g_bar = get_grade_tier_colors(subj.letter_grade)
        pct_clamped = min(max(subj.percentage, 0.0), 100.0)
        rows.append(
            f"<tr>"
            f"<td><strong>{html.escape(subj.name)}</strong></td>"
            f"<td class='rc-num'>{subj.marks_obtained:g} <span style='color:#94a3b8;'>/ {subj.max_marks:g}</span></td>"
            f"<td class='rc-num'>{subj.credits:g}</td>"
            f"<td class='rc-num'>"
            f"<div class='pct-bar-wrap'>"
            f"<strong>{subj.percentage:.2f}%</strong>"
            f"<div class='pct-bar-track'><div class='pct-bar-fill' style='width:{pct_clamped:.1f}%;background:{g_bar};'></div></div>"
            f"</div>"
            f"</td>"
            f"<td class='rc-center'><span class='grade-badge' style='background:{g_bg};color:{g_fg};'>{html.escape(subj.letter_grade)}</span></td>"
            f"<td class='rc-num'><strong>{subj.gpa_points:.1f}</strong></td>"
            f"<td class='rc-center'><span class='{pill_cls}'>{pill_icon} {html.escape(subj.status)}</span></td>"
            f"</tr>"
        )

    passed_count = sum(1 for s in summary.subjects if s.passed)
    total_courses = len(summary.subjects)

    return (
        f"<div class='report-card-box'>"
        f"<div class='rc-top-accent'></div>"
        f"<div class='rc-body'>"
        f"<div class='rc-header'>"
        f"<div class='rc-brand'>"
        f"<div class='rc-crest'>🎓</div>"
        f"<div>"
        f"<p class='rc-school'>{html.escape(summary.school_name)}</p>"
        f"<p class='rc-sub'>Official Academic Transcript &amp; Report Card &bull; Issued {html.escape(today_str)}</p>"
        f"</div>"
        f"</div>"
        f"<div class='rc-badge-group'>"
        f"<div class='{banner_cls}'>{banner_icon} STATUS: {banner_label} ({html.escape(summary.status)})</div>"
        f"<div class='honor-pill'>🏅 {html.escape(standing_label)}</div>"
        f"</div>"
        f"</div>"
        f"<div class='rc-meta'>"
        f"<div class='rc-meta-item'><span class='rc-meta-label'>Student Full Name</span><span class='rc-meta-val'>{html.escape(summary.student_name)}</span></div>"
        f"<div class='rc-meta-item'><span class='rc-meta-label'>Student ID / Roll No.</span><span class='rc-meta-val'>{html.escape(summary.student_id)}</span></div>"
        f"<div class='rc-meta-item'><span class='rc-meta-label'>Grade / Year Level</span><span class='rc-meta-val'>{html.escape(summary.grade_level)}</span></div>"
        f"<div class='rc-meta-item'><span class='rc-meta-label'>Academic Term</span><span class='rc-meta-val'>{html.escape(summary.term)}</span></div>"
        f"</div>"
        f"<div class='kpi-grid'>"
        f"<div class='kpi-card'>"
        f"<div class='kpi-card-top' style='background:#2563eb;'></div>"
        f"<div class='kpi-label'>Percent Grade</div>"
        f"<div class='kpi-value'>{summary.overall_percentage:.2f}%</div>"
        f"<div class='kpi-sub'>{summary.total_marks_obtained:g} / {summary.total_max_marks:g} Total Marks</div>"
        f"</div>"
        f"<div class='kpi-card' style='background:{overall_bg};'>"
        f"<div class='kpi-card-top' style='background:{overall_bar};'></div>"
        f"<div class='kpi-label'>Letter Grade</div>"
        f"<div class='kpi-value' style='color:{overall_fg};'>{html.escape(summary.overall_letter_grade)}</div>"
        f"<div class='kpi-sub'>{html.escape(standing_label)}</div>"
        f"</div>"
        f"<div class='kpi-card'>"
        f"<div class='kpi-card-top' style='background:#4f46e5;'></div>"
        f"<div class='kpi-label'>Cumulative GPA</div>"
        f"<div class='kpi-value'>{summary.gpa:.2f}</div>"
        f"<div class='kpi-sub'>4.00 Scale &bull; {summary.total_credits:g} Credits</div>"
        f"</div>"
        f"<div class='kpi-card'>"
        f"<div class='kpi-card-top' style='background:{status_bar};'></div>"
        f"<div class='kpi-label'>Pass / Fail Status</div>"
        f"<div class='kpi-value' style='color:{status_color};'>{html.escape(summary.status)}</div>"
        f"<div class='kpi-sub'>{passed_count} of {total_courses} Courses Passed</div>"
        f"</div>"
        f"</div>"
        f"<table class='rc-table'>"
        f"<thead>"
        f"<tr>"
        f"<th>Subject / Course</th>"
        f"<th class='rc-num'>Marks Obtained</th>"
        f"<th class='rc-num'>Credits</th>"
        f"<th class='rc-num'>Percent Grade</th>"
        f"<th class='rc-center'>Letter Grade</th>"
        f"<th class='rc-num'>GPA Pts</th>"
        f"<th class='rc-center'>Standing</th>"
        f"</tr>"
        f"</thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        f"<tfoot>"
        f"<tr>"
        f"<td>Cumulative Total ({total_courses} Subjects)</td>"
        f"<td class='rc-num'>{summary.total_marks_obtained:g} / {summary.total_max_marks:g}</td>"
        f"<td class='rc-num'>{summary.total_credits:g}</td>"
        f"<td class='rc-num'>{summary.overall_percentage:.2f}%</td>"
        f"<td class='rc-center'>{html.escape(summary.overall_letter_grade)}</td>"
        f"<td class='rc-num'>{summary.gpa:.2f}</td>"
        f"<td class='rc-center'>{html.escape(summary.status)}</td>"
        f"</tr>"
        f"</tfoot>"
        f"</table>"
        f"<div class='rc-remarks'>"
        f"<strong>Pass/Fail Determination:</strong> {html.escape(summary.status_reason)}<br>"
        f"<strong>Academic Advisor Remarks:</strong> {html.escape(summary.remarks)}"
        f"</div>"
        f"</div>"
        f"</div>"
    )


def _render_analytics_chart_html(summary: ReportCardSummary, passing_percentage: float) -> str:
    """Render a visual horizontal bar chart comparing subject percentages against passing cutoff."""
    cutoff_clamped = min(max(passing_percentage, 0.0), 100.0)
    bars_html = []
    for subj in summary.subjects:
        _, _, bar_color = get_grade_tier_colors(subj.letter_grade)
        pct_clamped = min(max(subj.percentage, 0.0), 100.0)
        bars_html.append(
            f"<div class='chart-row'>"
            f"<div class='chart-subj' title='{html.escape(subj.name)}'>{html.escape(subj.name)}</div>"
            f"<div class='chart-track'>"
            f"<div class='chart-cutoff' style='left:{cutoff_clamped:.1f}%;' title='Passing Threshold ({passing_percentage:g}%)'></div>"
            f"<div class='chart-fill' style='width:{pct_clamped:.1f}%;background:{bar_color};'></div>"
            f"</div>"
            f"<div class='chart-val'>{subj.percentage:.1f}% ({html.escape(subj.letter_grade)})</div>"
            f"</div>"
        )

    best_subj = max(summary.subjects, key=lambda s: s.percentage)
    low_subj = min(summary.subjects, key=lambda s: s.percentage)

    return (
        f"<div class='analytics-card'>"
        f"<div class='analytics-header'>"
        f"<p class='analytics-title'>📊 Subject Performance Distribution</p>"
        f"<div class='analytics-legend'>"
        f"🔴 Passing Cutoff: <strong>{passing_percentage:g}%</strong> &nbsp;|&nbsp; "
        f"🏆 Highest: <strong>{html.escape(best_subj.name)} ({best_subj.percentage:.1f}%)</strong> &nbsp;|&nbsp; "
        f"📌 Lowest: <strong>{html.escape(low_subj.name)} ({low_subj.percentage:.1f}%)</strong>"
        f"</div>"
        f"</div>"
        f"{''.join(bars_html)}"
        f"</div>"
    )


def _render_login_portal() -> None:
    """Render the 3-tier login and account registration portal."""
    st.markdown(
        "<div class='hero-banner'>"
        "<div class='hero-top'>"
        "<div>"
        "<div class='hero-badge'>🔒 Role-Based Academic Portal</div>"
        "<h1 class='main-title'>🎓 Student Grade &amp; Report Card Generator</h1>"
        "<p class='sub-title'>Sign in as a <strong>Student</strong>, <strong>Teacher</strong>, or "
        "<strong>Administrator</strong> to access role-specific grading tools, class rosters, "
        "school-wide analytics, and official report cards.</p>"
        "</div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    login_col, register_col = st.columns(2)

    with login_col:
        with _card_container():
            st.markdown(
                "<p class='auth-card-title'>🔑 Sign In to Your Account</p>"
                "<p class='auth-card-sub'>Choose a role or enter your username &amp; password</p>",
                unsafe_allow_html=True,
            )
            login_username = st.text_input(
                "Username",
                placeholder="e.g., alex, teacher, or admin",
                key="login_username_input",
            )
            login_password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter password",
                key="login_password_input",
            )
            if st.button("🔑 Sign In", type="primary", use_container_width=True):
                matched = authenticate_user(
                    st.session_state.users,
                    login_username,
                    login_password,
                )
                if matched is not None:
                    _login_as(matched)
                    st.rerun()
                else:
                    st.error("Invalid username or password. Use a demo account below!")

            st.divider()
            st.caption("⚡ **One-Click Demo Logins (3 Account Types)**")
            dcol1, dcol2, dcol3 = st.columns(3)
            with dcol1:
                if st.button("🎓 Student Login", use_container_width=True):
                    _login_as(st.session_state.users["alex"])
                    st.rerun()
            with dcol2:
                if st.button("👩‍🏫 Teacher Login", use_container_width=True):
                    _login_as(st.session_state.users["teacher"])
                    st.rerun()
            with dcol3:
                if st.button("🛡️ Admin Login", use_container_width=True):
                    _login_as(st.session_state.users["admin"])
                    st.rerun()

            st.markdown(
                "<div class='demo-creds-box'>"
                "<strong>3 Pre-configured Role Logins:</strong><br>"
                "1️⃣ <strong>Student:</strong> <span class='Demo-code'>alex</span> / <span class='Demo-code'>student123</span> "
                "(or <span class='Demo-code'>sam</span> / <span class='Demo-code'>priya</span>)<br>"
                "2️⃣ <strong>Teacher:</strong> <span class='Demo-code'>teacher</span> / <span class='Demo-code'>teacher123</span> "
                "<em>(Class roster selector, edit &amp; save student marks, custom advisor remarks)</em><br>"
                "3️⃣ <strong>Administrator:</strong> <span class='Demo-code'>admin</span> / <span class='Demo-code'>admin123</span> "
                "<em>(All Teacher features + School Policy &amp; Grade Curve, User Account Manager, School-Wide Analytics &amp; Master CSV Export)</em>"
                "</div>",
                unsafe_allow_html=True,
            )

    with register_col:
        with _card_container():
            st.markdown(
                "<p class='auth-card-title'>✨ Create New Account</p>"
                "<p class='auth-card-sub'>Register a Student, Teacher, or Administrator profile</p>",
                unsafe_allow_html=True,
            )
            reg_full_name = st.text_input(
                "Full Name",
                placeholder="e.g., Jordan Taylor",
                key="reg_full_name_input",
            )
            rcol1, rcol2 = st.columns(2)
            with rcol1:
                reg_username = st.text_input(
                    "Choose Username",
                    placeholder="e.g., jordan",
                    key="reg_username_input",
                )
            with rcol2:
                reg_role = st.selectbox(
                    "Account Type / Role",
                    options=list(VALID_ROLES),
                    index=0,
                    key="reg_role_select",
                )
            rcol3, rcol4 = st.columns(2)
            with rcol3:
                reg_student_id = st.text_input(
                    "Student / Staff ID",
                    value="STU-2026-305",
                    key="reg_student_id_input",
                )
            with rcol4:
                reg_grade_level = st.text_input(
                    "Grade Level / Title",
                    value="Grade 11",
                    key="reg_grade_level_input",
                )
            reg_school_name = st.text_input(
                "School / Institution Name",
                value=DEFAULT_SCHOOL,
                placeholder="e.g., Westview Academy of Arts & Sciences",
                key="reg_school_name_input",
            )
            st.caption("📚 **Core Subjects Included:** History, Science, Math, English")
            ecol1, ecol2 = st.columns(2)
            with ecol1:
                reg_elective_1 = st.selectbox(
                    "Choose 1st Elective",
                    options=list(ELECTIVE_OPTIONS),
                    index=0,
                    key="reg_elective_1_select",
                )
            with ecol2:
                reg_elective_2 = st.selectbox(
                    "Choose 2nd Elective",
                    options=list(ELECTIVE_OPTIONS),
                    index=1,
                    key="reg_elective_2_select",
                )
            reg_password = st.text_input(
                "Create Password (min. 6 characters)",
                type="password",
                placeholder="At least 6 characters",
                key="reg_password_input",
            )
            if st.button("✨ Create Account & Sign In", use_container_width=True):
                new_user, err_msg = register_user(
                    st.session_state.users,
                    username=reg_username,
                    password=reg_password,
                    full_name=reg_full_name,
                    role=reg_role,
                    student_id=reg_student_id,
                    grade_level=reg_grade_level,
                    school_name=reg_school_name,
                    electives=(reg_elective_1, reg_elective_2),
                )
                if err_msg:
                    st.error(err_msg)
                elif new_user is not None:
                    if new_user.role == ROLE_STUDENT and new_user.student_id not in st.session_state.roster:
                        st.session_state.roster[new_user.student_id] = {
                            "student_name": new_user.full_name,
                            "student_id": new_user.student_id,
                            "grade_level": new_user.grade_level,
                            "school_name": new_user.school_name,
                            "username": new_user.username,
                            "electives": [reg_elective_1, reg_elective_2],
                            "is_demo": False,
                            "custom_remarks": "",
                            "subjects": build_empty_student_subjects(reg_elective_1, reg_elective_2),
                        }
                    _login_as(new_user)
                    st.rerun()


def main() -> None:
    """Render the Streamlit Student Grade & Report Card Generator."""
    _init_state()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    current_user: UserAccount | None = st.session_state.current_user
    if current_user is None:
        _render_login_portal()
        return

    policy = st.session_state.school_policy
    is_admin = current_user.role == ROLE_ADMIN
    is_staff = current_user.role in (ROLE_TEACHER, ROLE_ADMIN)

    # Sidebar: User Session & Grading Settings
    with st.sidebar:
        st.markdown(_render_user_profile_html(current_user), unsafe_allow_html=True)
        if st.button("🚪 Sign Out", use_container_width=True):
            _logout_user()
            st.rerun()

        st.divider()
        st.header("⚙️ Grading Settings")
        scale = st.selectbox(
            "Grading Scale",
            options=[SCALE_PLUS_MINUS, SCALE_STANDARD],
            index=0 if policy["scale"] == SCALE_PLUS_MINUS else 1,
            disabled=not is_staff,
            help="Teachers and Administrators can change the grading scale.",
        )
        passing_percentage = st.slider(
            "Minimum Passing Percentage (%)",
            min_value=35,
            max_value=80,
            value=int(policy["passing_percentage"]),
            step=1,
            disabled=not is_admin,
            help="Locked to school policy (editable by Administrator).",
        )
        require_all_subjects_pass = st.checkbox(
            "Require passing every individual subject",
            value=bool(policy["require_all_subjects_pass"]),
            disabled=not is_admin,
            help="Locked to school policy (editable by Administrator).",
        )
        use_credit_weights = st.checkbox(
            "Weight overall percentage by subject credits",
            value=bool(policy["use_credit_weights"]),
            disabled=not is_staff,
            help="Enable if subjects carry different credit hours.",
        )
        policy["scale"] = scale
        policy["passing_percentage"] = passing_percentage
        policy["require_all_subjects_pass"] = require_all_subjects_pass
        policy["use_credit_weights"] = use_credit_weights

        st.divider()
        st.subheader("📊 Grade Scale Reference")
        st.markdown(
            _render_sidebar_scale_html(scale, int(passing_percentage)),
            unsafe_allow_html=True,
        )

    # Hero Banner with Live Settings Overview
    weight_mode_label = "Credit-Weighted" if use_credit_weights else "Total Marks"
    pass_rule_label = "All Courses Required" if require_all_subjects_pass else "Overall Average Only"
    curve_bonus = float(policy.get("grade_curve_bonus", 0.0))
    st.markdown(
        f"<div class='hero-banner'>"
        f"<div class='hero-top'>"
        f"<div>"
        f"<div class='hero-badge'>✨ Signed in as {html.escape(current_user.full_name)} ({html.escape(current_user.role)})</div>"
        f"<h1 class='main-title'>🎓 Student Grade &amp; Report Card Generator</h1>"
        f"<p class='sub-title'>Enter student details and course marks below to instantaneously calculate "
        f"<strong>Percent Grades</strong>, <strong>Letter Grades</strong>, <strong>Cumulative GPA</strong>, "
        f"and generate a print-ready <strong>Official Pass / Fail Report Card</strong>.</p>"
        f"</div>"
        f"</div>"
        f"<div class='hero-pills'>"
        f"<div class='hero-pill'>📏 Scale: <span>{html.escape(scale)}</span></div>"
        f"<div class='hero-pill'>🎯 Passing Cutoff: <span>{passing_percentage}%</span></div>"
        f"<div class='hero-pill'>⚖️ Calculation: <span>{weight_mode_label}</span></div>"
        f"<div class='hero-pill'>🛡️ Pass Rule: <span>{pass_rule_label}</span></div>"
        f"<div class='hero-pill'>📈 Curve Bonus: <span>+{curve_bonus:g}%</span></div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Administrator Exclusive Control Center
    if is_admin:
        with st.expander("🛡️ Administrator Control Center (School Policy, User Directory & Master Analytics)", expanded=True):
            adm_col1, adm_col2 = st.columns(2)
            with adm_col1:
                st.markdown("**🏛️ Institutional Policy & Grade Curve**")
                policy["school_name"] = st.text_input(
                    "Global School / Institution Name",
                    value=str(policy["school_name"]),
                    key="admin_school_name",
                )
                policy["grade_curve_bonus"] = st.slider(
                    "School-Wide Grade Curve Bonus (+ Marks)",
                    min_value=0.0,
                    max_value=10.0,
                    value=float(policy.get("grade_curve_bonus", 0.0)),
                    step=0.5,
                    help="Adds bonus points (capped at Max Marks) to every student's courses.",
                )
            with adm_col2:
                st.markdown("**👥 Registered Accounts & Role Management**")
                acct_summary = ", ".join(
                    f"`{u.username}` ({u.role})" for u in st.session_state.users.values()
                )
                st.caption(f"Active Accounts ({len(st.session_state.users)}): {acct_summary}")
                del_target = st.selectbox(
                    "Select User Account to Remove",
                    options=[u for u in st.session_state.users if u != current_user.username],
                    key="admin_del_user_select",
                )
                if st.button("🗑️ Delete Selected Account", use_container_width=True):
                    ok, msg = delete_user_account(
                        st.session_state.users, del_target, current_user.username
                    )
                    if ok:
                        st.rerun()
                    else:
                        st.error(msg)

            # School-Wide Master Roster CSV Export
            master_buf = io.StringIO()
            m_writer = csv.writer(master_buf)
            m_writer.writerow(["Student ID", "Student Name", "School", "Grade Level", "Overall %", "Letter Grade", "GPA", "Status"])
            for sid, srec in st.session_state.roster.items():
                s_school = str(srec.get("school_name", policy["school_name"]))
                raw_subjs = srec.get("subjects", [])
                if not raw_subjs:
                    m_writer.writerow([sid, str(srec["student_name"]), s_school, str(srec["grade_level"]), "N/A", "N/A", "N/A", "No Grades Yet"])
                    continue
                s_inputs = [
                    SubjectInput(
                        name=str(r["name"]),
                        marks_obtained=min(float(r["marks"]) + float(policy["grade_curve_bonus"]), float(r["max_marks"])),
                        max_marks=float(r["max_marks"]),
                        credits=float(r["credits"]),
                    )
                    for r in raw_subjs  # type: ignore[union-attr]
                ]
                s_sum = calculate_report_card(
                    s_inputs,
                    student_name=str(srec["student_name"]),
                    student_id=sid,
                    grade_level=str(srec["grade_level"]),
                    school_name=s_school,
                    passing_percentage=float(passing_percentage),
                    scale=scale,
                    require_all_subjects_pass=require_all_subjects_pass,
                    use_credit_weights=use_credit_weights,
                )
                m_writer.writerow([sid, s_sum.student_name, s_school, s_sum.grade_level, f"{s_sum.overall_percentage:.2f}%", s_sum.overall_letter_grade, f"{s_sum.gpa:.2f}", s_sum.status])
            st.download_button(
                "📥 Download Master School Roster & Grades (.csv)",
                data=master_buf.getvalue().encode("utf-8"),
                file_name="master_school_roster_grades.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # Teacher & Admin Classroom Roster Selector (Teachers see students in their own school)
    active_rec = st.session_state.roster.get(st.session_state.active_student_id, {})
    custom_advisor_remark = str(active_rec.get("custom_remarks", ""))
    if is_staff:
        with st.expander("👩‍🏫 Teacher Classroom Roster & Advisor Controls", expanded=True):
            if is_admin:
                roster_ids = list(st.session_state.roster.keys())
                st.caption(f"🛡️ **Administrator View:** Showing all {len(roster_ids)} students across all schools")
            else:
                teacher_school = current_user.school_name.strip().lower()
                roster_ids = [
                    sid
                    for sid, srec in st.session_state.roster.items()
                    if str(srec.get("school_name", DEFAULT_SCHOOL)).strip().lower() == teacher_school
                ]
                st.caption(
                    f"🏫 **School Roster Filter:** Showing {len(roster_ids)} student(s) enrolled at **{current_user.school_name}**"
                )
            if not roster_ids:
                roster_ids = list(st.session_state.roster.keys())
            r_labels = [
                f"{sid} — {st.session_state.roster[sid]['student_name']} ({st.session_state.roster[sid]['grade_level']} • {st.session_state.roster[sid].get('school_name', DEFAULT_SCHOOL)})"
                for sid in roster_ids
            ]
            curr_idx = (
                roster_ids.index(st.session_state.active_student_id)
                if st.session_state.active_student_id in roster_ids
                else 0
            )
            tcol1, tcol2, tcol3 = st.columns([3.0, 1.5, 1.5])
            with tcol1:
                chosen_label = st.selectbox(
                    "Select Student from School Roster",
                    options=r_labels,
                    index=curr_idx,
                    key="teacher_roster_select",
                )
                chosen_sid = chosen_label.split(" — ")[0]
            with tcol2:
                if st.button("📂 Load Student", use_container_width=True):
                    _load_student_from_roster(chosen_sid)
                    st.rerun()
            with tcol3:
                if st.button("💾 Save Marks to Roster", use_container_width=True):
                    if chosen_sid in st.session_state.roster:
                        st.session_state.roster[chosen_sid]["subjects"] = [
                            dict(r) for r in st.session_state.subjects
                        ]
            custom_advisor_remark = st.text_input(
                "Custom Teacher / Advisor Remark (optional override on Report Card)",
                value=custom_advisor_remark,
                placeholder="e.g., Excellent lab participation this semester!",
                key="teacher_custom_remark",
            )
            if chosen_sid in st.session_state.roster:
                st.session_state.roster[chosen_sid]["custom_remarks"] = custom_advisor_remark

    student_name = (
        current_user.full_name
        if current_user.role == ROLE_STUDENT
        else str(active_rec.get("student_name", "Alex Johnson"))
    )
    student_id = (
        current_user.student_id
        if current_user.role == ROLE_STUDENT
        else str(active_rec.get("student_id", "STU-2026-104"))
    )
    grade_level = (
        current_user.grade_level
        if current_user.role == ROLE_STUDENT
        else str(active_rec.get("grade_level", "Grade 11"))
    )
    term = str(policy["term"])
    school_name = (
        current_user.school_name
        if current_user.role == ROLE_STUDENT
        else str(active_rec.get("school_name", policy["school_name"]))
    )

    # Top Page Navigation Bar
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button(
            "📝 Coursework & Subject Marks",
            type="primary" if st.session_state.active_page == "marks" else "secondary",
            use_container_width=True,
        ):
            st.session_state.active_page = "marks"
            st.rerun()
    with nav_col2:
        if st.button(
            "🎓 Official Student Report Card & Analytics",
            type="primary" if st.session_state.active_page == "report" else "secondary",
            use_container_width=True,
        ):
            st.session_state.active_page = "report"
            st.session_state.show_report = True
            st.rerun()

    st.write("")

    # Identify lowest-percentage subject for "Remove Lowest Grade" preview
    lowest_row = None
    if len(st.session_state.subjects) > 1:
        lowest_row = min(
            st.session_state.subjects,
            key=lambda r: (float(r["marks"]) / max(float(r["max_marks"]), 1.0)) * 100.0,
        )

    # Page 1: Coursework & Assignment Marks (Editable ONLY by Teacher; Read-Only Table for Students)
    can_edit_grades = current_user.role == ROLE_TEACHER
    if st.session_state.active_page == "marks":
        mode_note = (
            "Read-Only Gradebook (Only your Teacher can add or change assignment grades)"
            if not can_edit_grades
            else f"Teacher Gradebook — Editing Student: <strong>{html.escape(student_name)}</strong> ({html.escape(student_id)})"
        )
        st.markdown(
            "<div class='section-head'>"
            "<div class='section-title-wrap'>"
            "<span class='step-pill'>Page 1</span>"
            "<h2 class='section-title'>Coursework &amp; Assignment Marks</h2>"
            "</div>"
            f"<span class='section-sub'>{mode_note}</span>"
            "</div>",
            unsafe_allow_html=True,
        )

        with _card_container():
            # Student Electives Selection (Core: History, Science, Math, English + 2 Student-Chosen Electives)
            target_sid = (
                current_user.student_id
                if current_user.role == ROLE_STUDENT
                else st.session_state.active_student_id
            )
            student_rec = st.session_state.roster.get(target_sid, {})
            saved_electives = student_rec.get("electives", ["Computer Science", "Art & Design"])
            cur_e1 = (
                str(saved_electives[0])
                if isinstance(saved_electives, (list, tuple)) and len(saved_electives) >= 1
                else "Computer Science"
            )
            cur_e2 = (
                str(saved_electives[1])
                if isinstance(saved_electives, (list, tuple)) and len(saved_electives) >= 2
                else "Art & Design"
            )
            st.markdown(
                f"<div class='demo-creds-box' style='margin-top:0;margin-bottom:14px;'>"
                f"📚 <strong>Required Core Subjects (4):</strong> "
                f"<span class='Demo-code'>History</span> &bull; "
                f"<span class='Demo-code'>Science</span> &bull; "
                f"<span class='Demo-code'>Math</span> &bull; "
                f"<span class='Demo-code'>English</span>"
                f" &nbsp;|&nbsp; 🎨 <strong>Chosen Electives (2):</strong> "
                f"<strong>{html.escape(cur_e1)}</strong> &amp; <strong>{html.escape(cur_e2)}</strong>"
                f"</div>",
                unsafe_allow_html=True,
            )
            el_col1, el_col2, el_col3 = st.columns([2.2, 2.2, 1.6])
            e1_idx = list(ELECTIVE_OPTIONS).index(cur_e1) if cur_e1 in ELECTIVE_OPTIONS else 0
            e2_idx = list(ELECTIVE_OPTIONS).index(cur_e2) if cur_e2 in ELECTIVE_OPTIONS else 1
            with el_col1:
                picked_e1 = st.selectbox(
                    "Choose 1st Elective Subject",
                    options=list(ELECTIVE_OPTIONS),
                    index=e1_idx,
                    key="portal_elective_1",
                )
            with el_col2:
                picked_e2 = st.selectbox(
                    "Choose 2nd Elective Subject",
                    options=list(ELECTIVE_OPTIONS),
                    index=e2_idx,
                    key="portal_elective_2",
                )
            with el_col3:
                st.write("")
                if st.button("✅ Save 2 Electives", use_container_width=True):
                    desired_names = get_student_subject_names(picked_e1, picked_e2)
                    if target_sid in st.session_state.roster:
                        st.session_state.roster[target_sid]["electives"] = [picked_e1, picked_e2]
                    while len(st.session_state.subjects) < 6:
                        _add_subject_row(
                            name=desired_names[len(st.session_state.subjects)],
                            marks=85.0,
                            max_marks=100.0,
                            credits=1.0,
                        )
                    for idx_s, s_name in enumerate(desired_names):
                        if idx_s < len(st.session_state.subjects):
                            st.session_state.subjects[idx_s]["name"] = s_name
                    if target_sid in st.session_state.roster:
                        st.session_state.roster[target_sid]["subjects"] = [
                            dict(r) for r in st.session_state.subjects
                        ]
                    st.rerun()

            if not st.session_state.subjects and not can_edit_grades:
                st.warning(
                    "📋 No assignments or test results have been entered by your teacher yet. "
                    "Once a teacher at your school inputs and saves your grades, they will appear here."
                )
            elif not can_edit_grades:
                # Pure Read-Only HTML Table for Students (zero input widgets so grades cannot be changed)
                ro_rows = []
                active_for_avg = []
                for row in st.session_state.subjects:
                    rid = int(row["id"])
                    is_dropped_row = (
                        bool(st.session_state.drop_lowest_grade)
                        and lowest_row is not None
                        and int(lowest_row["id"]) == rid
                    )
                    sub_assigns = row.get("assignments")
                    if isinstance(sub_assigns, list) and sub_assigns:
                        score_val = round(
                            sum(float(a["score"]) for a in sub_assigns) / len(sub_assigns),
                            2,
                        )
                        row["marks"] = score_val
                        assign_summary = ", ".join(
                            f"{html.escape(str(a.get('title', 'Assignment')))}: {float(a['score']):g}/100"
                            for a in sub_assigns
                        )
                    else:
                        score_val = float(row["marks"])
                        assign_summary = f"Course Score: {score_val:g}/100"
                    pct_val = round((score_val / 100.0) * 100.0, 2)
                    letter, _ = get_letter_grade_and_gpa(
                        pct_val, passing_percentage=float(passing_percentage), scale=scale
                    )
                    g_bg, g_fg, _ = get_grade_tier_colors(letter)
                    if is_dropped_row:
                        status_html = "<span class='honor-pill'>Dropped (Excluded)</span>"
                    else:
                        active_for_avg.append(pct_val)
                        passed_row = pct_val >= float(passing_percentage)
                        p_cls = "pill-pass" if passed_row else "pill-fail"
                        p_lbl = "✓ PASS" if passed_row else "✕ FAIL"
                        status_html = f"<span class='{p_cls}'>{p_lbl}</span>"
                    ro_rows.append(
                        f"<tr>"
                        f"<td><strong>{html.escape(str(row['name']))}</strong><br>"
                        f"<span style='font-size:0.78rem;color:#64748b;'>{assign_summary}</span></td>"
                        f"<td class='rc-num'><strong>{score_val:g} / 100</strong></td>"
                        f"<td class='rc-num'>{pct_val:.1f}%</td>"
                        f"<td class='rc-center'><span class='grade-badge' style='background:{g_bg};color:{g_fg};'>{html.escape(letter)}</span></td>"
                        f"<td class='rc-center'>{status_html}</td>"
                        f"</tr>"
                    )
                avg_pct = round(sum(active_for_avg) / len(active_for_avg), 2) if active_for_avg else 0.0
                avg_letter, _ = get_letter_grade_and_gpa(
                    avg_pct, passing_percentage=float(passing_percentage), scale=scale
                )
                st.markdown(
                    "<table class='rc-table'>"
                    "<thead><tr>"
                    "<th>Subject &amp; Assignments</th>"
                    "<th class='rc-num'>Averaged Score (/ 100)</th>"
                    "<th class='rc-num'>Subject %</th>"
                    "<th class='rc-center'>Letter Grade</th>"
                    "<th class='rc-center'>Status</th>"
                    "</tr></thead>"
                    f"<tbody>{''.join(ro_rows)}</tbody>"
                    "<tfoot><tr>"
                    f"<td>Final Averaged Grade ({len(active_for_avg)} Subjects)</td>"
                    f"<td class='rc-num'>{avg_pct:g} / 100</td>"
                    f"<td class='rc-num'>{avg_pct:.2f}%</td>"
                    f"<td class='rc-center'>{html.escape(avg_letter)}</td>"
                    f"<td class='rc-center'>{'PASS' if avg_pct >= float(passing_percentage) else 'FAIL'}</td>"
                    "</tr></tfoot>"
                    "</table>",
                    unsafe_allow_html=True,
                )
            else:
                # Teacher-Only Assignment Editor: Add assignments (/100) to any of the student's 6 subjects
                subject_names_list = [str(r["name"]) for r in st.session_state.subjects]
                st.markdown("**➕ Add Assignment to Student's Subject (Scored Over 100)**")
                add_c1, add_c2, add_c3, add_c4 = st.columns([2.2, 2.8, 1.8, 1.5])
                with add_c1:
                    target_subj_name = st.selectbox(
                        "Subject",
                        options=subject_names_list or list(CORE_SUBJECTS),
                        key="teacher_add_assign_subj",
                    )
                with add_c2:
                    new_assign_title = st.text_input(
                        "Assignment Title",
                        value="Unit Test",
                        key="teacher_add_assign_title",
                    )
                with add_c3:
                    new_assign_score = st.number_input(
                        "Score (/ 100 %)",
                        min_value=0.0,
                        max_value=100.0,
                        value=88.0,
                        step=1.0,
                        key="teacher_add_assign_score",
                    )
                with add_c4:
                    st.write("")
                    if st.button("➕ Add Assignment", use_container_width=True):
                        for r in st.session_state.subjects:
                            if str(r["name"]) == target_subj_name:
                                assigns = list(r.get("assignments") or [])  # type: ignore[arg-type]
                                assigns.append(
                                    {
                                        "id": len(assigns) + 1,
                                        "title": f"{target_subj_name} — {new_assign_title.strip() or 'Assignment'}",
                                        "score": float(new_assign_score),
                                    }
                                )
                                r["assignments"] = assigns
                                r["marks"] = round(
                                    sum(float(a["score"]) for a in assigns) / len(assigns),
                                    2,
                                )
                                break
                        if st.session_state.active_student_id in st.session_state.roster:
                            st.session_state.roster[st.session_state.active_student_id]["subjects"] = [
                                dict(r) for r in st.session_state.subjects
                            ]
                        st.rerun()

                st.divider()
                hdr1, hdr2, hdr3, hdr4 = st.columns([4.2, 2.2, 1.8, 0.8])
                hdr1.markdown("**Subject (4 Core + 2 Electives)**")
                hdr2.markdown("**Averaged Score (/ 100 %)**")
                hdr3.markdown("**Subject Grade**")
                hdr4.markdown("**Del**")

                for row in list(st.session_state.subjects):
                    rid = int(row["id"])
                    row["max_marks"] = 100.0
                    row["credits"] = 1.0
                    c1, c2, c3, c4 = st.columns([4.2, 2.2, 1.8, 0.8])
                    with c1:
                        row["name"] = st.text_input(
                            f"Subject Name {rid}",
                            value=str(row["name"]),
                            key=f"subj_name_{rid}",
                            label_visibility="collapsed",
                        )
                        sub_assigns = row.get("assignments")
                        if isinstance(sub_assigns, list) and sub_assigns:
                            st.caption(
                                "Assignments: "
                                + " | ".join(
                                    f"{a.get('title', 'Task')}: **{float(a['score']):g}/100**"
                                    for a in sub_assigns
                                )
                            )
                    with c2:
                        row["marks"] = st.number_input(
                            f"Score over 100 {rid}",
                            min_value=0.0,
                            max_value=100.0,
                            value=min(float(row["marks"]), 100.0),
                            step=1.0,
                            key=f"subj_marks_{rid}",
                            label_visibility="collapsed",
                        )
                    with c3:
                        st.markdown(
                            _render_live_row_badge(
                                float(row["marks"]),
                                100.0,
                                float(passing_percentage),
                                scale,
                            ),
                            unsafe_allow_html=True,
                        )
                    with c4:
                        if st.button(
                            "✕",
                            key=f"subj_del_{rid}",
                            help="Remove this subject",
                            disabled=len(st.session_state.subjects) <= 1,
                        ):
                            _remove_subject_row(rid)
                            if st.session_state.active_student_id in st.session_state.roster:
                                st.session_state.roster[st.session_state.active_student_id]["subjects"] = [
                                    dict(r) for r in st.session_state.subjects
                                ]
                            st.rerun()

                # Auto-sync teacher edits to the active student's roster record
                if st.session_state.active_student_id in st.session_state.roster:
                    st.session_state.roster[st.session_state.active_student_id]["subjects"] = [
                        dict(r) for r in st.session_state.subjects
                    ]

                st.write("")
                btn_col1, btn_col2, _ = st.columns([2.2, 2.2, 4.6])
                with btn_col1:
                    if st.button("🧹 Clear Scores", use_container_width=True):
                        _clear_all_marks()
                        st.rerun()
                with btn_col2:
                    if st.button("🔄 Reset 6 Subjects", use_container_width=True):
                        _reset_sample_subjects()
                        st.rerun()
                st.write("")

            # Demo-only button to re-roll random assignments & test results
            if current_user.username in DEMO_STUDENT_USERNAMES:
                if st.button(
                    "🎲 Generate New Random Demo Assignments & Test Results",
                    use_container_width=True,
                ):
                    new_demo_rows = generate_random_demo_assignments(6, (cur_e1, cur_e2))
                    st.session_state.roster[current_user.student_id]["subjects"] = new_demo_rows
                    st.session_state.subjects = [dict(r) for r in new_demo_rows]
                    st.session_state.drop_lowest_grade = False
                    st.rerun()

            # Button to Remove / Restore Lowest Grade to preview impact
            if lowest_row is not None:
                low_pct = (float(lowest_row["marks"]) / max(float(lowest_row["max_marks"]), 1.0)) * 100.0
                if not st.session_state.drop_lowest_grade:
                    if st.button(
                        f"📉 Remove Lowest Grade ({lowest_row['name']} — {low_pct:.1f}%) to See Result",
                        use_container_width=True,
                    ):
                        st.session_state.drop_lowest_grade = True
                        st.session_state.show_report = True
                        st.session_state.active_page = "report"
                        st.rerun()
                else:
                    if st.button(
                        f"🔄 Restore Lowest Grade ({lowest_row['name']} — {low_pct:.1f}%)",
                        use_container_width=True,
                    ):
                        st.session_state.drop_lowest_grade = False
                        st.rerun()

            st.write("")
            if st.button(
                "🎓 Calculate Grades & Generate Report Card",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.show_report = True
                st.session_state.active_page = "report"
                st.rerun()

    # Page 2: Official Student Report Card & Analytics
    if st.session_state.active_page == "report":
        active_rows = list(st.session_state.subjects)
        if st.session_state.drop_lowest_grade and lowest_row is not None and len(active_rows) > 1:
            active_rows = [r for r in active_rows if int(r["id"]) != int(lowest_row["id"])]
            low_pct = (float(lowest_row["marks"]) / max(float(lowest_row["max_marks"]), 1.0)) * 100.0
            st.markdown(
                f"<div class='demo-creds-box' style='margin-bottom:14px;'>"
                f"📉 <strong>Lowest Grade Removed Preview:</strong> Excluded "
                f"<strong>{html.escape(str(lowest_row['name']))}</strong> ({low_pct:.1f}%) "
                f"to show your recalculated GPA and Report Card result."
                f"</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                f"🔄 Restore Lowest Grade ({lowest_row['name']} — {low_pct:.1f}%)",
                use_container_width=True,
            ):
                st.session_state.drop_lowest_grade = False
                st.rerun()
        elif lowest_row is not None:
            low_pct = (float(lowest_row["marks"]) / max(float(lowest_row["max_marks"]), 1.0)) * 100.0
            if st.button(
                f"📉 Remove Lowest Grade ({lowest_row['name']} — {low_pct:.1f}%) to See Result",
                use_container_width=True,
            ):
                st.session_state.drop_lowest_grade = True
                st.rerun()

        subject_inputs = [
            SubjectInput(
                name=str(r["name"]),
                marks_obtained=min(
                    float(r["marks"]) + curve_bonus,
                    float(r["max_marks"]),
                ),
                max_marks=float(r["max_marks"]),
                credits=float(r["credits"]),
            )
            for r in active_rows
        ]

        validation_errors = validate_subjects(subject_inputs)
        if validation_errors:
            for err in validation_errors:
                st.error(err)
            return

        summary = calculate_report_card(
            subject_inputs,
            student_name=student_name,
            student_id=student_id,
            grade_level=grade_level,
            term=term,
            school_name=school_name,
            passing_percentage=float(passing_percentage),
            scale=scale,
            require_all_subjects_pass=require_all_subjects_pass,
            use_credit_weights=use_credit_weights,
        )
        if custom_advisor_remark.strip():
            from dataclasses import replace

            summary = replace(
                summary,
                remarks=f"{summary.remarks} | Advisor Note: {custom_advisor_remark.strip()}",
            )

        st.markdown(
            "<div class='section-head'>"
            "<div class='section-title-wrap'>"
            "<span class='step-pill'>Page 2</span>"
            "<h2 class='section-title'>Official Student Report Card &amp; Analytics</h2>"
            "</div>"
            "<span class='section-sub'>Ready for download or printing</span>"
            "</div>",
            unsafe_allow_html=True,
        )

        today_str = date.today().strftime("%B %d, %Y")
        st.markdown(_render_report_card_html(summary, today_str), unsafe_allow_html=True)

        # Visual Subject Distribution Chart
        st.markdown(
            _render_analytics_chart_html(summary, float(passing_percentage)),
            unsafe_allow_html=True,
        )

        # Export / Download Actions
        st.write("")
        dl_col1, dl_col2 = st.columns(2)
        safe_slug = (
            "".join(ch if ch.isalnum() else "_" for ch in summary.student_name)
            .strip("_")
            .lower()
            or "student"
        )
        with dl_col1:
            html_bytes = export_report_card_html(summary, today_str).encode("utf-8")
            st.download_button(
                label="🖨️ Download Printable Report Card (.html)",
                data=html_bytes,
                file_name=f"report_card_{safe_slug}.html",
                mime="text/html",
                use_container_width=True,
            )
        with dl_col2:
            csv_bytes = export_report_card_csv(summary).encode("utf-8")
            st.download_button(
                label="📥 Download Report Card Data (.csv)",
                data=csv_bytes,
                file_name=f"report_card_{safe_slug}.csv",
                mime="text/csv",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
