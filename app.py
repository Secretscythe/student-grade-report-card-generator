"""Streamlit Web App: Student Grade & Report Card Generator."""

from __future__ import annotations

import csv
import hmac
import html
import io
from contextlib import nullcontext
from dataclasses import replace
from datetime import date
from typing import Any

import streamlit as st

from auth import (
    ALL_SUBJECT_OPTIONS,
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
    find_user_by_username_or_email,
    generate_random_demo_assignments,
    generate_recovery_code,
    get_configured_resend_api_key,
    get_default_student_roster,
    get_default_users,
    get_student_subject_names,
    register_user,
    reset_user_password,
    send_resend_recovery_email,
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
    color: #0f172a;
  }

  .block-container {
    max-width: 1080px !important;
    padding-top: 1.75rem !important;
    padding-bottom: 3.5rem !important;
  }

  /* Clean Compact Top Banner */
  .hero-banner {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 60%, #2563eb 100%);
    border-radius: 16px;
    padding: 24px 30px;
    color: #ffffff;
    box-shadow: 0 12px 28px -10px rgba(15, 23, 42, 0.22);
    margin-bottom: 20px;
  }
  .hero-badge {
    display: inline-block;
    background: rgba(255, 255, 255, 0.16);
    color: #e0e7ff;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 4px 12px;
    border-radius: 999px;
    margin-bottom: 8px;
  }
  .main-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.85rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0 0 4px 0;
    line-height: 1.25;
  }
  .sub-title {
    font-size: 0.95rem;
    color: #e2e8f0;
    margin: 0;
    line-height: 1.5;
  }
  .hero-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 14px;
  }
  .hero-pill {
    background: rgba(15, 23, 42, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.18);
    color: #f8fafc;
    border-radius: 8px;
    padding: 5px 12px;
    font-size: 0.82rem;
    font-weight: 600;
  }
  .hero-pill span {
    color: #93c5fd;
    font-weight: 700;
  }

  /* Card Containers */
  [data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff;
    border-radius: 14px !important;
    border: 1px solid #cbd5e1 !important;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04) !important;
    padding: 12px !important;
  }

  .card-heading {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.2rem;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 4px 0;
  }
  .card-subheading {
    font-size: 0.88rem;
    color: #475569;
    margin: 0 0 14px 0;
  }

  .info-strip {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-left: 4px solid #2563eb;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.9rem;
    color: #1e293b;
    margin-bottom: 14px;
    line-height: 1.55;
  }
  .code-tag {
    background: #e2e8f0;
    color: #0f172a;
    padding: 2px 7px;
    border-radius: 6px;
    font-family: monospace;
    font-weight: 700;
    font-size: 0.84rem;
  }

  /* Sidebar Profile Card */
  .user-profile-box {
    background: #ffffff;
    border: 1px solid #cbd5e1;
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
    margin-bottom: 8px;
  }
  .user-profile-name {
    font-weight: 800;
    font-size: 0.98rem;
    color: #0f172a;
  }
  .role-badge-student {
    background: #dbeafe;
    color: #1e40af;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    padding: 3px 9px;
    border-radius: 999px;
  }
  .role-badge-instructor {
    background: #ede9fe;
    color: #5b21b6;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    padding: 3px 9px;
    border-radius: 999px;
  }
  .role-badge-admin {
    background: #fef3c7;
    color: #92400e;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    padding: 3px 9px;
    border-radius: 999px;
  }
  .user-profile-meta {
    font-size: 0.84rem;
    color: #334155;
    line-height: 1.6;
  }

  /* Clean High-Legibility Tables */
  .rc-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    margin: 12px 0 18px 0;
    font-size: 0.94rem;
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    overflow: hidden;
    background: #ffffff;
  }
  .rc-table th {
    background: #0f172a;
    color: #ffffff;
    padding: 12px 16px;
    text-align: left;
    font-weight: 700;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .rc-table td {
    padding: 13px 16px;
    border-bottom: 1px solid #e2e8f0;
    color: #0f172a;
    vertical-align: middle;
  }
  .rc-table tbody tr:nth-child(even) {
    background: #f8fafc;
  }
  .rc-table tfoot td {
    background: #f1f5f9;
    font-weight: 800;
    color: #0f172a;
    border-top: 2px solid #94a3b8;
    border-bottom: none;
    font-size: 0.96rem;
  }
  .rc-num { text-align: right !important; }
  .rc-center { text-align: center !important; }

  .grade-badge {
    display: inline-block;
    min-width: 38px;
    padding: 4px 10px;
    border-radius: 8px;
    font-weight: 800;
    font-size: 0.86rem;
    text-align: center;
  }
  .pill-pass {
    background: #dcfce7;
    color: #166534;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 800;
    display: inline-block;
  }
  .pill-fail {
    background: #fee2e2;
    color: #991b1b;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 800;
    display: inline-block;
  }
  .honor-pill {
    background: #f1f5f9;
    color: #334155;
    border: 1px solid #cbd5e1;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    display: inline-block;
  }

  /* Sidebar Scale Table */
  .scale-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.84rem;
    background: #ffffff;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #cbd5e1;
  }
  .scale-table th {
    background: #f1f5f9;
    color: #334155;
    font-size: 0.74rem;
    text-transform: uppercase;
    padding: 8px 10px;
    text-align: left;
    border-bottom: 1px solid #cbd5e1;
  }
  .scale-table td {
    padding: 7px 10px;
    border-bottom: 1px solid #f1f5f9;
    color: #0f172a;
    font-weight: 500;
  }
  .scale-chip {
    display: inline-block;
    min-width: 32px;
    text-align: center;
    padding: 2px 7px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 0.78rem;
  }

  /* Report Card Box */
  .report-card-box {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 12px 32px -12px rgba(15, 23, 42, 0.12);
    margin-top: 8px;
    color: #0f172a;
  }
  .rc-top-accent {
    height: 7px;
    background: linear-gradient(90deg, #1e3a8a 0%, #2563eb 50%, #4f46e5 100%);
  }
  .rc-body {
    padding: 28px 32px;
  }
  .rc-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 16px;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 18px;
    margin-bottom: 20px;
  }
  .rc-school {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.45rem;
    font-weight: 800;
    color: #0f172a;
    margin: 0 !important;
  }
  .rc-sub {
    font-size: 0.88rem;
    color: #475569;
    margin: 4px 0 0 0 !important;
  }
  .status-banner-pass {
    background: #ecfdf5;
    color: #065f46;
    border: 1.5px solid #6ee7b7;
    padding: 7px 18px;
    border-radius: 999px;
    font-weight: 800;
    font-size: 0.88rem;
  }
  .status-banner-fail {
    background: #fef2f2;
    color: #991b1b;
    border: 1.5px solid #fca5a5;
    padding: 7px 18px;
    border-radius: 999px;
    font-weight: 800;
    font-size: 0.88rem;
  }
  .rc-meta {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px 18px;
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 20px;
  }
  .rc-meta-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #475569;
    font-weight: 700;
    display: block;
  }
  .rc-meta-val {
    font-size: 0.96rem;
    font-weight: 800;
    color: #0f172a;
  }
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 14px;
    margin-bottom: 22px;
  }
  .kpi-card {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
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
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #475569;
    font-weight: 700;
    margin-bottom: 6px;
  }
  .kpi-value {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.75rem;
    font-weight: 800;
    color: #0f172a;
  }
  .kpi-sub {
    font-size: 0.8rem;
    color: #475569;
    margin-top: 4px;
    font-weight: 600;
  }
  .rc-remarks {
    border: 1px solid #bfdbfe;
    border-left: 5px solid #2563eb;
    background: #eff6ff;
    padding: 14px 18px;
    border-radius: 10px;
    font-size: 0.92rem;
    line-height: 1.6;
    color: #0f172a;
  }

  /* Subject Distribution Bars */
  .analytics-card {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 14px;
    padding: 20px 24px;
    margin-top: 18px;
    color: #0f172a;
  }
  .chart-row {
    display: grid;
    grid-template-columns: 170px 1fr 95px;
    align-items: center;
    gap: 14px;
    margin-bottom: 10px;
  }
  .chart-subj {
    font-size: 0.9rem;
    font-weight: 700;
    color: #0f172a;
  }
  .chart-track {
    position: relative;
    height: 12px;
    background: #e2e8f0;
    border-radius: 999px;
  }
  .chart-fill {
    height: 100%;
    border-radius: 999px;
  }
  .chart-cutoff {
    position: absolute;
    top: -3px;
    bottom: -3px;
    width: 2px;
    background: #dc2626;
  }
  .chart-val {
    text-align: right;
    font-size: 0.86rem;
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
        st.session_state.active_student_id = "20260104"
    if "school_policy" not in st.session_state:
        st.session_state.school_policy = {
            "school_name": DEFAULT_SCHOOL,
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
    if "recovery_pending" not in st.session_state:
        st.session_state.recovery_pending = None


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
            "assignments": [],
        }
    )


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
    """Render a clean grade scale reference table for the sidebar."""
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
    subj_line = (
        f"<br>📘 Subject: <strong>{html.escape(user.teaching_subject)}</strong>"
        if user.role == ROLE_TEACHER
        else ""
    )
    return (
        f"<div class='user-profile-box'>"
        f"<div class='user-profile-top'>"
        f"<span class='user-profile-name'>{icon} {html.escape(user.full_name)}</span>"
        f"<span class='{role_cls}'>{html.escape(user.role)}</span>"
        f"</div>"
        f"<div class='user-profile-meta'>"
        f"🪪 ID: <strong>{html.escape(user.student_id)}</strong> &bull; {html.escape(user.grade_level)}<br>"
        f"🏫 {html.escape(user.school_name)}"
        f"{subj_line}"
        f"</div>"
        f"</div>"
    )


def _render_subjects_table_html(
    subjects: list[dict[str, object]],
    *,
    passing_percentage: float,
    scale: str,
    drop_lowest_id: int | None = None,
    highlight_subject: str | None = None,
) -> str:
    """Render a clean, legible HTML table of the student's 6 subjects and assignment averages."""
    rows_html = []
    active_scores: list[float] = []

    for row in subjects:
        rid = int(row["id"])
        subj_name = str(row["name"])
        is_dropped = drop_lowest_id is not None and rid == drop_lowest_id
        is_teacher_subj = (
            highlight_subject is not None
            and subj_name.strip().lower() == highlight_subject.strip().lower()
        )

        sub_assigns = row.get("assignments")
        if isinstance(sub_assigns, list) and sub_assigns:
            score_val = round(
                sum(float(a["score"]) for a in sub_assigns) / len(sub_assigns),
                2,
            )
            row["marks"] = score_val
            assign_text = " &bull; ".join(
                f"{html.escape(str(a.get('title', 'Task')).split(' — ')[-1])}: <strong>{float(a['score']):g}/100</strong>"
                for a in sub_assigns
            )
        else:
            score_val = float(row["marks"])
            assign_text = (
                f"Recorded Score: <strong>{score_val:g}/100</strong>"
                if score_val > 0
                else "<em>No assignments graded yet</em>"
            )

        letter, _ = get_letter_grade_and_gpa(
            score_val, passing_percentage=passing_percentage, scale=scale
        )
        g_bg, g_fg, _ = get_grade_tier_colors(letter)

        if is_dropped:
            status_html = "<span class='honor-pill'>Dropped (Lowest)</span>"
        else:
            active_scores.append(score_val)
            passed = score_val >= passing_percentage
            p_cls = "pill-pass" if passed else "pill-fail"
            p_lbl = "✓ PASS" if passed else "✕ FAIL"
            status_html = f"<span class='{p_cls}'>{p_lbl}</span>"

        owner_tag = ""
        if highlight_subject is not None:
            owner_tag = (
                " <span class='role-badge-instructor' style='margin-left:6px;'>Your Subject</span>"
                if is_teacher_subj
                else " <span style='font-size:0.75rem;color:#64748b;margin-left:6px;'>🔒 Other Teacher</span>"
            )

        row_style = " style='background:#eff6ff;'" if is_teacher_subj else ""
        rows_html.append(
            f"<tr{row_style}>"
            f"<td><strong>{html.escape(subj_name)}</strong>{owner_tag}</td>"
            f"<td style='color:#334155;font-size:0.86rem;'>{assign_text}</td>"
            f"<td class='rc-num'><strong>{score_val:g} / 100</strong> ({score_val:.1f}%)</td>"
            f"<td class='rc-center'><span class='grade-badge' style='background:{g_bg};color:{g_fg};'>{html.escape(letter)}</span></td>"
            f"<td class='rc-center'>{status_html}</td>"
            f"</tr>"
        )

    avg_pct = round(sum(active_scores) / len(active_scores), 2) if active_scores else 0.0
    avg_letter, _ = get_letter_grade_and_gpa(
        avg_pct, passing_percentage=passing_percentage, scale=scale
    )
    overall_status = "PASS" if avg_pct >= passing_percentage else "FAIL"

    return (
        "<table class='rc-table'>"
        "<thead><tr>"
        "<th>Subject</th>"
        "<th>Assignments (Score / 100)</th>"
        "<th class='rc-num'>Subject Average</th>"
        "<th class='rc-center'>Grade</th>"
        "<th class='rc-center'>Status</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody>"
        "<tfoot><tr>"
        f"<td colspan='2'>Overall Final Average ({len(active_scores)} Active Subjects)</td>"
        f"<td class='rc-num'>{avg_pct:.2f} / 100 ({avg_pct:.2f}%)</td>"
        f"<td class='rc-center'>{html.escape(avg_letter)}</td>"
        f"<td class='rc-center'>{overall_status}</td>"
        "</tr></tfoot>"
        "</table>"
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
        g_bg, g_fg, _ = get_grade_tier_colors(subj.letter_grade)
        rows.append(
            f"<tr>"
            f"<td><strong>{html.escape(subj.name)}</strong></td>"
            f"<td class='rc-num'><strong>{subj.marks_obtained:g} / {subj.max_marks:g}</strong></td>"
            f"<td class='rc-num'><strong>{subj.percentage:.2f}%</strong></td>"
            f"<td class='rc-center'><span class='grade-badge' style='background:{g_bg};color:{g_fg};'>{html.escape(subj.letter_grade)}</span></td>"
            f"<td class='rc-num'>{subj.gpa_points:.1f}</td>"
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
        f"<div>"
        f"<p class='rc-school'>🎓 {html.escape(summary.school_name)}</p>"
        f"<p class='rc-sub'>Official Student Report Card &bull; Issued {html.escape(today_str)}</p>"
        f"</div>"
        f"<div style='text-align:right;'>"
        f"<span class='{banner_cls}'>{banner_icon} {banner_label} ({html.escape(summary.status)})</span> "
        f"<span class='honor-pill'>🏅 {html.escape(standing_label)}</span>"
        f"</div>"
        f"</div>"
        f"<div class='rc-meta'>"
        f"<div><span class='rc-meta-label'>Student Name</span><span class='rc-meta-val'>{html.escape(summary.student_name)}</span></div>"
        f"<div><span class='rc-meta-label'>8-Digit Student ID</span><span class='rc-meta-val'>{html.escape(summary.student_id)}</span></div>"
        f"<div><span class='rc-meta-label'>Grade Level</span><span class='rc-meta-val'>{html.escape(summary.grade_level)}</span></div>"
        f"<div><span class='rc-meta-label'>Academic Term</span><span class='rc-meta-val'>{html.escape(summary.term)}</span></div>"
        f"</div>"
        f"<div class='kpi-grid'>"
        f"<div class='kpi-card'>"
        f"<div class='kpi-card-top' style='background:#2563eb;'></div>"
        f"<div class='kpi-label'>Overall Average</div>"
        f"<div class='kpi-value'>{summary.overall_percentage:.2f}%</div>"
        f"<div class='kpi-sub'>{summary.total_marks_obtained:g} / {summary.total_max_marks:g} Total Score</div>"
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
        f"<div class='kpi-sub'>4.00 Scale</div>"
        f"</div>"
        f"<div class='kpi-card'>"
        f"<div class='kpi-card-top' style='background:{status_bar};'></div>"
        f"<div class='kpi-label'>Final Standing</div>"
        f"<div class='kpi-value' style='color:{status_color};'>{html.escape(summary.status)}</div>"
        f"<div class='kpi-sub'>{passed_count} of {total_courses} Subjects Passed</div>"
        f"</div>"
        f"</div>"
        f"<table class='rc-table'>"
        f"<thead><tr>"
        f"<th>Subject</th>"
        f"<th class='rc-num'>Score (/ 100)</th>"
        f"<th class='rc-num'>Percent Grade</th>"
        f"<th class='rc-center'>Letter Grade</th>"
        f"<th class='rc-num'>GPA Pts</th>"
        f"<th class='rc-center'>Status</th>"
        f"</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        f"<tfoot><tr>"
        f"<td>Final Cumulative Summary ({total_courses} Subjects)</td>"
        f"<td class='rc-num'>{summary.total_marks_obtained:g} / {summary.total_max_marks:g}</td>"
        f"<td class='rc-num'>{summary.overall_percentage:.2f}%</td>"
        f"<td class='rc-center'>{html.escape(summary.overall_letter_grade)}</td>"
        f"<td class='rc-num'>{summary.gpa:.2f}</td>"
        f"<td class='rc-center'>{html.escape(summary.status)}</td>"
        f"</tr></tfoot>"
        f"</table>"
        f"<div class='rc-remarks'>"
        f"<strong>Pass/Fail Determination:</strong> {html.escape(summary.status_reason)}<br>"
        f"<strong>Academic Advisor Remarks:</strong> {html.escape(summary.remarks)}"
        f"</div>"
        f"</div>"
        f"</div>"
    )


def _render_analytics_chart_html(summary: ReportCardSummary, passing_percentage: float) -> str:
    """Render a clean horizontal bar chart comparing subject scores against the passing cutoff."""
    cutoff_clamped = min(max(passing_percentage, 0.0), 100.0)
    bars_html = []
    for subj in summary.subjects:
        _, _, bar_color = get_grade_tier_colors(subj.letter_grade)
        pct_clamped = min(max(subj.percentage, 0.0), 100.0)
        bars_html.append(
            f"<div class='chart-row'>"
            f"<div class='chart-subj'>{html.escape(subj.name)}</div>"
            f"<div class='chart-track'>"
            f"<div class='chart-cutoff' style='left:{cutoff_clamped:.1f}%;'></div>"
            f"<div class='chart-fill' style='width:{pct_clamped:.1f}%;background:{bar_color};'></div>"
            f"</div>"
            f"<div class='chart-val'>{subj.percentage:.1f}% ({html.escape(subj.letter_grade)})</div>"
            f"</div>"
        )

    return (
        f"<div class='analytics-card'>"
        f"<p class='card-heading' style='font-size:1.05rem;margin-bottom:14px;'>"
        f"📊 Subject Performance Comparison (Red Line = {passing_percentage:g}% Passing Cutoff)"
        f"</p>"
        f"{''.join(bars_html)}"
        f"</div>"
    )


def _render_login_portal() -> None:
    """Render a clean, legible 3-tier login and account registration portal."""
    st.markdown(
        "<div class='hero-banner'>"
        "<div class='hero-badge'>🔒 Academic Grading &amp; Report Card Portal</div>"
        "<h1 class='main-title'>🎓 Student Grade &amp; Report Card Generator</h1>"
        "<p class='sub-title'>Sign in as a <strong>Student</strong>, <strong>Teacher</strong>, or "
        "<strong>Administrator</strong>, or create a new account below.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    login_col, register_col = st.columns(2)

    with login_col:
        with _card_container():
            st.markdown(
                "<p class='card-heading'>🔑 Sign In</p>"
                "<p class='card-subheading'>Enter your username and password, or use a 1-click demo login</p>",
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
                    st.error("Invalid username or password. Try one of the demo buttons below!")

            st.divider()
            st.caption("⚡ **Quick Demo Logins** (Pre-loaded with random test assignments)")
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

            st.caption(
                "Demo credentials: `alex` / `student123` • `teacher` / `teacher123` • `admin` / `admin123`"
            )

            # Forgot Password / Email Recovery via Resend
            with st.expander("📧 Forgot Password? Send Recovery Code via Email"):
                secret_resend_key = ""
                try:
                    secrets_obj = getattr(st, "secrets", None)
                    if secrets_obj and "RESEND_API_KEY" in secrets_obj:
                        secret_resend_key = str(secrets_obj["RESEND_API_KEY"])
                except Exception:  # noqa: BLE001
                    secret_resend_key = ""
                active_resend_key = get_configured_resend_api_key(secret_resend_key)

                rec_identifier = st.text_input(
                    "Username or Account Email",
                    placeholder="e.g., alex or teacher",
                    key="rec_identifier_input",
                )
                rec_email_override = st.text_input(
                    "Email Address to Receive 6-Digit Code",
                    placeholder="Enter your email address",
                    key="rec_email_override_input",
                )
                if st.button("📨 Send 6-Digit Recovery Code", use_container_width=True):
                    target_acct = find_user_by_username_or_email(
                        st.session_state.users,
                        rec_identifier,
                    )
                    if target_acct is None:
                        st.error("No account found matching that username or email.")
                    else:
                        code = generate_recovery_code()
                        dest_email = rec_email_override.strip() or target_acct.email
                        st.session_state.recovery_pending = {
                            "username": target_acct.username,
                            "email": dest_email,
                            "code": code,
                        }
                        ok_sent, send_msg = send_resend_recovery_email(
                            api_key=active_resend_key,
                            to_email=dest_email,
                            full_name=target_acct.full_name,
                            username=target_acct.username,
                            code=code,
                        )
                        if ok_sent:
                            st.markdown(
                                f"<div class='info-strip'>✅ {html.escape(send_msg)}</div>",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.warning(send_msg)

                pending = st.session_state.recovery_pending
                if isinstance(pending, dict) and pending.get("username"):
                    st.divider()
                    entered_code = st.text_input(
                        f"Enter 6-Digit Code for '{pending['username']}'",
                        placeholder="6-digit code from email",
                        key="rec_verify_code_input",
                    )
                    new_reset_pwd = st.text_input(
                        "New Password (min. 6 characters)",
                        type="password",
                        key="rec_new_password_input",
                    )
                    if st.button("🔐 Verify Code & Reset Password", type="primary", use_container_width=True):
                        expected_code = str(pending.get("code", ""))
                        if expected_code and hmac.compare_digest(entered_code.strip(), expected_code):
                            ok_rst, rst_msg = reset_user_password(
                                st.session_state.users,
                                str(pending["username"]),
                                new_reset_pwd,
                            )
                            if ok_rst:
                                st.session_state.recovery_pending = None
                                st.markdown(
                                    f"<div class='info-strip'>✅ {html.escape(rst_msg)}</div>",
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.error(rst_msg)
                        else:
                            st.error("Invalid 6-digit recovery code.")

    with register_col:
        with _card_container():
            st.markdown(
                "<p class='card-heading'>✨ Create New Account</p>"
                "<p class='card-subheading'>An 8-digit Student/Staff ID is assigned automatically</p>",
                unsafe_allow_html=True,
            )
            rcol1, rcol2 = st.columns(2)
            with rcol1:
                reg_role = st.selectbox(
                    "1. Account Role",
                    options=list(VALID_ROLES),
                    index=0,
                    key="reg_role_select",
                )
            with rcol2:
                reg_full_name = st.text_input(
                    "2. Full Name",
                    placeholder="e.g., Jordan Taylor",
                    key="reg_full_name_input",
                )

            rcol3, rcol4 = st.columns(2)
            with rcol3:
                reg_username = st.text_input(
                    "3. Username",
                    placeholder="e.g., jordan",
                    key="reg_username_input",
                )
            with rcol4:
                reg_password = st.text_input(
                    "4. Password (min. 6 chars)",
                    type="password",
                    placeholder="At least 6 characters",
                    key="reg_password_input",
                )

            rcol5, rcol6 = st.columns(2)
            with rcol5:
                reg_email = st.text_input(
                    "5. Recovery Email",
                    placeholder="e.g., jordan@email.com",
                    key="reg_email_input",
                )
            with rcol6:
                reg_grade_level = st.text_input(
                    "6. Grade Level / Title",
                    value="Grade 11" if reg_role == ROLE_STUDENT else "Faculty",
                    key="reg_grade_level_input",
                )

            reg_school_name = st.text_input(
                "7. School / Institution Name",
                value=DEFAULT_SCHOOL,
                key="reg_school_name_input",
            )

            reg_elective_1 = ELECTIVE_OPTIONS[0]
            reg_elective_2 = ELECTIVE_OPTIONS[1]
            reg_teaching_subject = "Math"

            if reg_role == ROLE_TEACHER:
                reg_teaching_subject = st.selectbox(
                    "8. Subject You Teach (Teachers control 1 subject)",
                    options=list(ALL_SUBJECT_OPTIONS),
                    index=2,
                    key="reg_teaching_subject_select",
                )
            elif reg_role == ROLE_STUDENT:
                st.caption("📚 **Core Subjects Included:** History, Science, Math, English")
                ecol1, ecol2 = st.columns(2)
                with ecol1:
                    reg_elective_1 = st.selectbox(
                        "8. Choose 1st Elective",
                        options=list(ELECTIVE_OPTIONS),
                        index=0,
                        key="reg_elective_1_select",
                    )
                with ecol2:
                    reg_elective_2 = st.selectbox(
                        "9. Choose 2nd Elective",
                        options=list(ELECTIVE_OPTIONS),
                        index=1,
                        key="reg_elective_2_select",
                    )

            if st.button("✨ Create Account & Sign In", use_container_width=True):
                new_user, err_msg = register_user(
                    st.session_state.users,
                    username=reg_username,
                    password=reg_password,
                    full_name=reg_full_name,
                    role=reg_role,
                    grade_level=reg_grade_level,
                    school_name=reg_school_name,
                    electives=(reg_elective_1, reg_elective_2),
                    email=reg_email,
                    teaching_subject=reg_teaching_subject,
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
    is_teacher = current_user.role == ROLE_TEACHER
    is_staff = is_teacher or is_admin

    scale = str(policy["scale"])
    passing_percentage = int(policy["passing_percentage"])
    require_all_subjects_pass = bool(policy["require_all_subjects_pass"])
    use_credit_weights = bool(policy["use_credit_weights"])

    # Clean Role-Specific Sidebar
    with st.sidebar:
        st.markdown(_render_user_profile_html(current_user), unsafe_allow_html=True)
        if st.button("🚪 Sign Out", use_container_width=True):
            _logout_user()
            st.rerun()

        if is_staff:
            st.divider()
            st.subheader("⚙️ Grading Controls")
            scale = st.selectbox(
                "Grading Scale",
                options=[SCALE_PLUS_MINUS, SCALE_STANDARD],
                index=0 if scale == SCALE_PLUS_MINUS else 1,
            )
            policy["scale"] = scale
            if is_admin:
                passing_percentage = st.slider(
                    "Passing Cutoff (%)",
                    min_value=35,
                    max_value=80,
                    value=passing_percentage,
                    step=1,
                )
                require_all_subjects_pass = st.checkbox(
                    "Require passing every subject",
                    value=require_all_subjects_pass,
                )
                policy["passing_percentage"] = passing_percentage
                policy["require_all_subjects_pass"] = require_all_subjects_pass

        st.divider()
        st.subheader("📊 Grade Scale")
        st.markdown(
            _render_sidebar_scale_html(scale, int(passing_percentage)),
            unsafe_allow_html=True,
        )

    curve_bonus = float(policy.get("grade_curve_bonus", 0.0))

    # Active Student Resolution
    if is_staff:
        if is_admin:
            roster_ids = list(st.session_state.roster.keys())
        else:
            teacher_school = current_user.school_name.strip().lower()
            roster_ids = [
                sid
                for sid, srec in st.session_state.roster.items()
                if str(srec.get("school_name", DEFAULT_SCHOOL)).strip().lower() == teacher_school
            ]
        if not roster_ids:
            roster_ids = list(st.session_state.roster.keys())
        if st.session_state.active_student_id not in roster_ids:
            _load_student_from_roster(roster_ids[0])

    active_rec = st.session_state.roster.get(st.session_state.active_student_id, {})
    student_name = (
        current_user.full_name
        if current_user.role == ROLE_STUDENT
        else str(active_rec.get("student_name", "Alex Johnson"))
    )
    student_id = (
        current_user.student_id
        if current_user.role == ROLE_STUDENT
        else str(active_rec.get("student_id", "20260104"))
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
    custom_advisor_remark = str(active_rec.get("custom_remarks", ""))

    # Compact Top Header
    st.markdown(
        f"<div class='hero-banner'>"
        f"<div class='hero-badge'>✨ {html.escape(current_user.role)} Portal &bull; {html.escape(school_name)}</div>"
        f"<h1 class='main-title'>🎓 {html.escape(student_name)} — Academic Gradebook</h1>"
        f"<div class='hero-pills'>"
        f"<div class='hero-pill'>🪪 Student ID: <span>{html.escape(student_id)}</span></div>"
        f"<div class='hero-pill'>🎓 Level: <span>{html.escape(grade_level)}</span></div>"
        f"<div class='hero-pill'>🎯 Passing Cutoff: <span>{passing_percentage}%</span></div>"
        f"<div class='hero-pill'>📏 Scale: <span>{html.escape(scale)}</span></div>"
        + (
            f"<div class='hero-pill'>📘 Teaching Subject: <span>{html.escape(current_user.teaching_subject)}</span></div>"
            if is_teacher
            else ""
        )
        + f"</div></div>",
        unsafe_allow_html=True,
    )

    # Top Page Switcher Buttons
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button(
            "📝 Page 1: Subjects & Assignments",
            type="primary" if st.session_state.active_page == "marks" else "secondary",
            use_container_width=True,
        ):
            st.session_state.active_page = "marks"
            st.rerun()
    with nav_col2:
        if st.button(
            "🎓 Page 2: Official Student Report Card & Analytics",
            type="primary" if st.session_state.active_page == "report" else "secondary",
            use_container_width=True,
        ):
            st.session_state.active_page = "report"
            st.session_state.show_report = True
            st.rerun()

    st.write("")

    # Staff Bar: Select Student (Teacher sees their school; Admin sees all schools + Admin tools)
    if is_staff:
        with _card_container():
            r_labels = [
                f"{sid} — {st.session_state.roster[sid]['student_name']} ({st.session_state.roster[sid]['grade_level']} • {st.session_state.roster[sid].get('school_name', DEFAULT_SCHOOL)})"
                for sid in roster_ids
            ]
            curr_idx = (
                roster_ids.index(st.session_state.active_student_id)
                if st.session_state.active_student_id in roster_ids
                else 0
            )
            scol1, scol2, scol3 = st.columns([3.2, 1.2, 2.6])
            with scol1:
                chosen_label = st.selectbox(
                    f"👩‍🏫 Select Student ({'All Schools' if is_admin else current_user.school_name})",
                    options=r_labels,
                    index=curr_idx,
                    key="teacher_roster_select",
                )
                chosen_sid = chosen_label.split(" — ")[0]
            with scol2:
                st.write("")
                if st.button("📂 Load Student", use_container_width=True):
                    _load_student_from_roster(chosen_sid)
                    st.rerun()
            with scol3:
                custom_advisor_remark = st.text_input(
                    "Advisor Remark on Report Card",
                    value=custom_advisor_remark,
                    placeholder="Optional note for student...",
                    key="teacher_custom_remark",
                )
                if chosen_sid in st.session_state.roster:
                    st.session_state.roster[chosen_sid]["custom_remarks"] = custom_advisor_remark

        if is_admin:
            with st.expander("🛡️ Administrator Tools (School Curve, Account Manager & Master CSV Export)"):
                adm_col1, adm_col2 = st.columns(2)
                with adm_col1:
                    policy["school_name"] = st.text_input(
                        "Default School Name",
                        value=str(policy["school_name"]),
                        key="admin_school_name",
                    )
                    policy["grade_curve_bonus"] = st.slider(
                        "School-Wide Curve Bonus (+% Marks)",
                        min_value=0.0,
                        max_value=10.0,
                        value=float(policy.get("grade_curve_bonus", 0.0)),
                        step=0.5,
                    )
                with adm_col2:
                    del_target = st.selectbox(
                        "Remove Registered Account",
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

    # Identify lowest-percentage subject for "Remove Lowest Grade" preview
    lowest_row = None
    if len(st.session_state.subjects) > 1:
        lowest_row = min(
            st.session_state.subjects,
            key=lambda r: (float(r["marks"]) / max(float(r["max_marks"]), 1.0)) * 100.0,
        )
    dropped_id = (
        int(lowest_row["id"])
        if st.session_state.drop_lowest_grade and lowest_row is not None
        else None
    )

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

    # =========================================================================
    # PAGE 1: SUBJECTS & ASSIGNMENTS
    # =========================================================================
    if st.session_state.active_page == "marks":
        with _card_container():
            st.markdown(
                f"<p class='card-heading'>📚 {html.escape(student_name)}'s 6 Subjects &amp; Assignments</p>"
                f"<p class='card-subheading'>Core Subjects: <strong>History, Science, Math, English</strong> &bull; "
                f"Chosen Electives: <strong>{html.escape(cur_e1)}, {html.escape(cur_e2)}</strong></p>",
                unsafe_allow_html=True,
            )

            # Teacher Single-Subject Assignment Control Box
            if is_teacher:
                teacher_subj = current_user.teaching_subject
                st.markdown(
                    f"<div class='info-strip'>"
                    f"👩‍🏫 <strong>Your Assigned Subject: <span class='code-tag'>{html.escape(teacher_subj)}</span></strong> &mdash; "
                    f"Add assignments scored out of 100 below. They automatically average into the student's <strong>{html.escape(teacher_subj)}</strong> grade."
                    f"</div>",
                    unsafe_allow_html=True,
                )
                ac1, ac2, ac3, ac4 = st.columns([3.2, 1.8, 1.8, 1.4])
                with ac1:
                    new_assign_title = st.text_input(
                        f"New {teacher_subj} Assignment Name",
                        value="Unit Test",
                        key="teacher_add_assign_title",
                    )
                with ac2:
                    new_assign_score = st.number_input(
                        "Score (/ 100 %)",
                        min_value=0.0,
                        max_value=100.0,
                        value=88.0,
                        step=1.0,
                        key="teacher_add_assign_score",
                    )
                with ac3:
                    st.write("")
                    if st.button(f"➕ Add to {teacher_subj}", type="primary", use_container_width=True):
                        matched_subj = False
                        for r in st.session_state.subjects:
                            if str(r["name"]).strip().lower() == teacher_subj.strip().lower():
                                matched_subj = True
                                assigns = list(r.get("assignments") or [])  # type: ignore[arg-type]
                                assigns.append(
                                    {
                                        "id": len(assigns) + 1,
                                        "title": f"{teacher_subj} — {new_assign_title.strip() or 'Assignment'}",
                                        "score": float(new_assign_score),
                                    }
                                )
                                r["assignments"] = assigns
                                r["marks"] = round(
                                    sum(float(a["score"]) for a in assigns) / len(assigns),
                                    2,
                                )
                                break
                        if not matched_subj:
                            _add_subject_row(
                                name=teacher_subj,
                                marks=float(new_assign_score),
                                max_marks=100.0,
                                credits=1.0,
                            )
                            st.session_state.subjects[-1]["assignments"] = [
                                {
                                    "id": 1,
                                    "title": f"{teacher_subj} — {new_assign_title.strip() or 'Assignment'}",
                                    "score": float(new_assign_score),
                                }
                            ]
                        if target_sid in st.session_state.roster:
                            st.session_state.roster[target_sid]["subjects"] = [
                                dict(r) for r in st.session_state.subjects
                            ]
                        st.rerun()
                with ac4:
                    st.write("")
                    if st.button(f"🧹 Clear {teacher_subj}", use_container_width=True):
                        for r in st.session_state.subjects:
                            if str(r["name"]).strip().lower() == teacher_subj.strip().lower():
                                r["marks"] = 0.0
                                r["assignments"] = []
                        if target_sid in st.session_state.roster:
                            st.session_state.roster[target_sid]["subjects"] = [
                                dict(r) for r in st.session_state.subjects
                            ]
                        st.rerun()

            # Clean Legible HTML Table of All 6 Subjects & Their Assignment Averages
            st.markdown(
                _render_subjects_table_html(
                    st.session_state.subjects,
                    passing_percentage=float(passing_percentage),
                    scale=scale,
                    drop_lowest_id=dropped_id,
                    highlight_subject=current_user.teaching_subject if is_teacher else None,
                ),
                unsafe_allow_html=True,
            )

            # Student Electives Picker (tucked neatly into a clean expander)
            with st.expander("🎨 Choose or Change the 2 Elective Subjects"):
                el_col1, el_col2, el_col3 = st.columns([2.2, 2.2, 1.6])
                e1_idx = list(ELECTIVE_OPTIONS).index(cur_e1) if cur_e1 in ELECTIVE_OPTIONS else 0
                e2_idx = list(ELECTIVE_OPTIONS).index(cur_e2) if cur_e2 in ELECTIVE_OPTIONS else 1
                with el_col1:
                    picked_e1 = st.selectbox(
                        "1st Elective Subject",
                        options=list(ELECTIVE_OPTIONS),
                        index=e1_idx,
                        key="portal_elective_1",
                    )
                with el_col2:
                    picked_e2 = st.selectbox(
                        "2nd Elective Subject",
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

            # Action Buttons Row (Drop Lowest Grade, Randomize Demo, View Report Card)
            act_col1, act_col2 = st.columns(2)
            with act_col1:
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
            with act_col2:
                if current_user.username in DEMO_STUDENT_USERNAMES:
                    if st.button(
                        "🎲 Generate New Random Demo Test Results",
                        use_container_width=True,
                    ):
                        new_demo_rows = generate_random_demo_assignments(6, (cur_e1, cur_e2))
                        st.session_state.roster[current_user.student_id]["subjects"] = new_demo_rows
                        st.session_state.subjects = [dict(r) for r in new_demo_rows]
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

    # =========================================================================
    # PAGE 2: OFFICIAL REPORT CARD & ANALYTICS
    # =========================================================================
    if st.session_state.active_page == "report":
        active_rows = list(st.session_state.subjects)
        if st.session_state.drop_lowest_grade and lowest_row is not None and len(active_rows) > 1:
            active_rows = [r for r in active_rows if int(r["id"]) != int(lowest_row["id"])]
            low_pct = (float(lowest_row["marks"]) / max(float(lowest_row["max_marks"]), 1.0)) * 100.0
            st.markdown(
                f"<div class='info-strip'>"
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
            summary = replace(
                summary,
                remarks=f"{summary.remarks} | Advisor Note: {custom_advisor_remark.strip()}",
            )

        today_str = date.today().strftime("%B %d, %Y")
        st.markdown(_render_report_card_html(summary, today_str), unsafe_allow_html=True)
        st.markdown(
            _render_analytics_chart_html(summary, float(passing_percentage)),
            unsafe_allow_html=True,
        )

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
