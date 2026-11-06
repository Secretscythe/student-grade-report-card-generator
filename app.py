"""Streamlit Web App: Student Grade & Report Card Generator."""

from __future__ import annotations

import csv
import html
import io
from datetime import date

import streamlit as st

from grading import (
    SCALE_PLUS_MINUS,
    SCALE_STANDARD,
    ReportCardSummary,
    SubjectInput,
    calculate_report_card,
    export_report_card_csv,
    export_report_card_html,
    validate_subjects,
)

st.set_page_config(
    page_title="Student Grade & Report Card Generator",
    page_icon="🎓",
    layout="wide",
)

CUSTOM_CSS = """
<style>
  .main-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: #1e3a8a;
    margin-bottom: 0.2rem;
  }
  .sub-title {
    font-size: 1.02rem;
    color: #475569;
    margin-bottom: 1.5rem;
  }
  .report-card-box {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 16px;
    padding: 28px;
    box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.08);
    margin-top: 12px;
    color: #0f172a;
  }
  .rc-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    border-bottom: 2px solid #1e3a8a;
    padding-bottom: 16px;
    margin-bottom: 20px;
  }
  .rc-school {
    font-size: 1.5rem;
    font-weight: 800;
    color: #1e3a8a;
    margin: 0;
  }
  .rc-sub {
    font-size: 0.9rem;
    color: #64748b;
    margin: 2px 0 0 0;
  }
  .status-banner-pass {
    background: #dcfce7;
    color: #166534;
    border: 1.5px solid #86efac;
    padding: 8px 20px;
    border-radius: 999px;
    font-weight: 800;
    font-size: 1rem;
    letter-spacing: 0.04em;
  }
  .status-banner-fail {
    background: #fee2e2;
    color: #991b1b;
    border: 1.5px solid #fca5a5;
    padding: 8px 20px;
    border-radius: 999px;
    font-weight: 800;
    font-size: 1rem;
    letter-spacing: 0.04em;
  }
  .rc-meta {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 10px 20px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 22px;
    font-size: 0.92rem;
  }
  .rc-meta span {
    color: #64748b;
    font-weight: 600;
  }
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 14px;
    margin-bottom: 24px;
  }
  .kpi-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
  }
  .kpi-label {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
    font-weight: 700;
    margin-bottom: 6px;
  }
  .kpi-value {
    font-size: 1.75rem;
    font-weight: 800;
    color: #0f172a;
  }
  .rc-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
    font-size: 0.94rem;
  }
  .rc-table th {
    background: #1e3a8a;
    color: #ffffff;
    padding: 11px 14px;
    text-align: left;
    font-weight: 600;
  }
  .rc-table td {
    padding: 11px 14px;
    border-bottom: 1px solid #e2e8f0;
    color: #1e293b;
  }
  .rc-num { text-align: right !important; }
  .rc-center { text-align: center !important; }
  .pill-pass {
    background: #dcfce7;
    color: #166534;
    padding: 3px 11px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
  }
  .pill-fail {
    background: #fee2e2;
    color: #991b1b;
    padding: 3px 11px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
  }
  .rc-remarks {
    border-left: 4px solid #1e3a8a;
    background: #eff6ff;
    padding: 14px 18px;
    border-radius: 0 10px 10px 0;
    font-size: 0.93rem;
    color: #1e293b;
  }
</style>
"""


DEFAULT_SUBJECTS: list[dict[str, object]] = [
    {"id": 1, "name": "Mathematics", "marks": 92.0, "max_marks": 100.0, "credits": 1.0},
    {"id": 2, "name": "Science", "marks": 86.0, "max_marks": 100.0, "credits": 1.0},
    {"id": 3, "name": "English Literature", "marks": 88.0, "max_marks": 100.0, "credits": 1.0},
    {"id": 4, "name": "World History", "marks": 79.0, "max_marks": 100.0, "credits": 1.0},
    {"id": 5, "name": "Computer Science", "marks": 95.0, "max_marks": 100.0, "credits": 1.0},
]


def _init_state() -> None:
    """Initialize Streamlit session state variables."""
    if "subjects" not in st.session_state:
        st.session_state.subjects = [dict(row) for row in DEFAULT_SUBJECTS]
    if "next_id" not in st.session_state:
        st.session_state.next_id = len(DEFAULT_SUBJECTS) + 1
    if "show_report" not in st.session_state:
        st.session_state.show_report = False


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
    st.session_state.show_report = False


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


def _render_report_card_html(summary: ReportCardSummary, today_str: str) -> str:
    """Build the styled visual report card HTML block for Streamlit."""
    banner_cls = "status-banner-pass" if summary.passed else "status-banner-fail"
    banner_label = "PASSED" if summary.passed else "FAILED"
    status_color = "#166534" if summary.passed else "#991b1b"

    rows = []
    for subj in summary.subjects:
        pill_cls = "pill-pass" if subj.passed else "pill-fail"
        rows.append(
            f"<tr>"
            f"<td><strong>{html.escape(subj.name)}</strong></td>"
            f"<td class='rc-num'>{subj.marks_obtained:g} / {subj.max_marks:g}</td>"
            f"<td class='rc-num'>{subj.credits:g}</td>"
            f"<td class='rc-num'><strong>{subj.percentage:.2f}%</strong></td>"
            f"<td class='rc-center'><strong>{html.escape(subj.letter_grade)}</strong></td>"
            f"<td class='rc-center'><span class='{pill_cls}'>{html.escape(subj.status)}</span></td>"
            f"</tr>"
        )

    return (
        f"<div class='report-card-box'>"
        f"  <div class='rc-header'>"
        f"    <div>"
        f"      <p class='rc-school'>🎓 {html.escape(summary.school_name)}</p>"
        f"      <p class='rc-sub'>Official Academic Report Card &bull; Issued {html.escape(today_str)}</p>"
        f"    </div>"
        f"    <div class='{banner_cls}'>STATUS: {banner_label} ({html.escape(summary.status)})</div>"
        f"  </div>"
        f"  <div class='rc-meta'>"
        f"    <div><span>Student Name:</span> {html.escape(summary.student_name)}</div>"
        f"    <div><span>Student ID:</span> {html.escape(summary.student_id)}</div>"
        f"    <div><span>Grade / Level:</span> {html.escape(summary.grade_level)}</div>"
        f"    <div><span>Academic Term:</span> {html.escape(summary.term)}</div>"
        f"  </div>"
        f"  <div class='kpi-grid'>"
        f"    <div class='kpi-card'>"
        f"      <div class='kpi-label'>Percent Grade</div>"
        f"      <div class='kpi-value'>{summary.overall_percentage:.2f}%</div>"
        f"    </div>"
        f"    <div class='kpi-card'>"
        f"      <div class='kpi-label'>Letter Grade</div>"
        f"      <div class='kpi-value'>{html.escape(summary.overall_letter_grade)}</div>"
        f"    </div>"
        f"    <div class='kpi-card'>"
        f"      <div class='kpi-label'>Pass / Fail Status</div>"
        f"      <div class='kpi-value' style='color:{status_color};'>{html.escape(summary.status)}</div>"
        f"    </div>"
        f"    <div class='kpi-card'>"
        f"      <div class='kpi-label'>Total Marks &bull; GPA</div>"
        f"      <div class='kpi-value'>{summary.total_marks_obtained:g}/{summary.total_max_marks:g} &bull; {summary.gpa:.2f}</div>"
        f"    </div>"
        f"  </div>"
        f"  <table class='rc-table'>"
        f"    <thead>"
        f"      <tr>"
        f"        <th>Subject</th>"
        f"        <th class='rc-num'>Marks Obtained</th>"
        f"        <th class='rc-num'>Credits</th>"
        f"        <th class='rc-num'>Percent Grade</th>"
        f"        <th class='rc-center'>Letter Grade</th>"
        f"        <th class='rc-center'>Pass / Fail</th>"
        f"      </tr>"
        f"    </thead>"
        f"    <tbody>{''.join(rows)}</tbody>"
        f"  </table>"
        f"  <div class='rc-remarks'>"
        f"    <strong>Pass/Fail Determination:</strong> {html.escape(summary.status_reason)}<br>"
        f"    <strong>Academic Remarks:</strong> {html.escape(summary.remarks)}"
        f"  </div>"
        f"</div>"
    )


def main() -> None:
    """Render the Streamlit Student Grade & Report Card Generator."""
    _init_state()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    st.markdown(
        "<div class='main-title'>🎓 Student Grade & Report Card Generator</div>"
        "<div class='sub-title'>Enter your subject marks below to calculate your "
        "<b>Percent Grade</b>, <b>Letter Grade</b>, <b>GPA</b>, and official "
        "<b>Pass / Fail Report Card</b>.</div>",
        unsafe_allow_html=True,
    )

    # Sidebar: Grading Rules & Settings
    with st.sidebar:
        st.header("⚙️ Grading Settings")
        scale = st.selectbox(
            "Grading Scale",
            options=[SCALE_PLUS_MINUS, SCALE_STANDARD],
            index=0,
            help="Choose between detailed Plus/Minus grades (A+ to F) or standard A–F.",
        )
        passing_percentage = st.slider(
            "Minimum Passing Percentage (%)",
            min_value=35,
            max_value=80,
            value=60,
            step=1,
            help="Minimum percentage required to pass.",
        )
        require_all_subjects_pass = st.checkbox(
            "Require passing every individual subject",
            value=True,
            help="When enabled, failing any single subject results in an overall FAIL status.",
        )
        use_credit_weights = st.checkbox(
            "Weight overall percentage by subject credits",
            value=False,
            help="Enable if subjects carry different credit hours.",
        )

        st.divider()
        st.subheader("📊 Grade Scale Reference")
        if scale == SCALE_PLUS_MINUS:
            st.caption(
                f"- **A+**: 97–100% | **A**: 93–96.9% | **A-**: 90–92.9%\n"
                f"- **B+**: 87–89.9% | **B**: 83–86.9% | **B-**: 80–82.9%\n"
                f"- **C+**: 77–79.9% | **C**: 73–76.9% | **C-**: 70–72.9%\n"
                f"- **D+ / D**: {passing_percentage}–69.9%\n"
                f"- **F (Fail)**: Below {passing_percentage}%"
            )
        else:
            st.caption(
                f"- **A**: 90–100% (4.0 GPA)\n"
                f"- **B**: 80–89.9% (3.0 GPA)\n"
                f"- **C**: 70–79.9% (2.0 GPA)\n"
                f"- **D**: {passing_percentage}–69.9% (1.0 GPA)\n"
                f"- **F (Fail)**: Below {passing_percentage}% (0.0 GPA)"
            )

    # Step 1: Student Details
    st.subheader("1. Student Information")
    info_col1, info_col2, info_col3, info_col4 = st.columns(4)
    with info_col1:
        student_name = st.text_input("Student Full Name", value="Alex Johnson")
    with info_col2:
        student_id = st.text_input("Student ID / Roll No.", value="STU-2026-104")
    with info_col3:
        grade_level = st.text_input("Grade / Year Level", value="Grade 11")
    with info_col4:
        term = st.text_input("Academic Term", value="Fall Semester 2026")

    school_name = st.text_input(
        "School / Institution Name",
        value="Westview Academy of Arts & Sciences",
    )

    # Optional CSV Import
    with st.expander("📂 Optional: Import Subject Marks from CSV"):
        st.caption(
            "Upload a CSV with columns `Subject`, `Marks`, `Max Marks` (optional), and `Credits` (optional)."
        )
        uploaded_file = st.file_uploader("Choose CSV file", type=["csv"])
        if uploaded_file is not None:
            try:
                content = uploaded_file.getvalue().decode("utf-8-sig")
                imported_rows = _parse_uploaded_csv(content)
                if imported_rows:
                    if st.button("Load Uploaded Subjects", type="secondary"):
                        st.session_state.subjects = imported_rows
                        st.session_state.next_id = max(r["id"] for r in imported_rows) + 1
                        st.session_state.show_report = True
                        st.rerun()
                else:
                    st.warning("No valid subject rows found in the uploaded CSV.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not parse CSV file: {exc}")

    # Step 2: Subject Marks Entry
    st.subheader("2. Enter Subject Marks")

    hdr1, hdr2, hdr3, hdr4, hdr5 = st.columns([3.2, 1.6, 1.6, 1.3, 0.7])
    hdr1.markdown("**Subject Name**")
    hdr2.markdown("**Marks Obtained**")
    hdr3.markdown("**Maximum Marks**")
    hdr4.markdown("**Credits**")
    hdr5.markdown("**Remove**")

    for row in list(st.session_state.subjects):
        rid = int(row["id"])
        c1, c2, c3, c4, c5 = st.columns([3.2, 1.6, 1.6, 1.3, 0.7])
        with c1:
            row["name"] = st.text_input(
                f"Subject Name {rid}",
                value=str(row["name"]),
                placeholder="e.g., Physics",
                key=f"subj_name_{rid}",
                label_visibility="collapsed",
            )
        with c2:
            row["marks"] = st.number_input(
                f"Marks Obtained {rid}",
                min_value=0.0,
                max_value=10000.0,
                value=float(row["marks"]),
                step=1.0,
                key=f"subj_marks_{rid}",
                label_visibility="collapsed",
            )
        with c3:
            row["max_marks"] = st.number_input(
                f"Max Marks {rid}",
                min_value=1.0,
                max_value=10000.0,
                value=float(row["max_marks"]),
                step=1.0,
                key=f"subj_max_{rid}",
                label_visibility="collapsed",
            )
        with c4:
            row["credits"] = st.number_input(
                f"Credits {rid}",
                min_value=0.5,
                max_value=20.0,
                value=float(row["credits"]),
                step=0.5,
                key=f"subj_cred_{rid}",
                label_visibility="collapsed",
            )
        with c5:
            if st.button(
                "✕",
                key=f"subj_del_{rid}",
                help="Remove this subject",
                disabled=len(st.session_state.subjects) <= 1,
            ):
                _remove_subject_row(rid)
                st.rerun()

    btn_col1, btn_col2, btn_col3, _ = st.columns([1.8, 1.8, 1.8, 3.6])
    with btn_col1:
        if st.button("➕ Add Subject", use_container_width=True):
            _add_subject_row(name=f"Subject {len(st.session_state.subjects) + 1}")
            st.rerun()
    with btn_col2:
        if st.button("🧹 Clear Marks", use_container_width=True):
            _clear_all_marks()
            st.rerun()
    with btn_col3:
        if st.button("🔄 Reset Sample Data", use_container_width=True):
            _reset_sample_subjects()
            st.rerun()

    st.write("")
    if st.button(
        "🎓 Calculate Grades & Generate Report Card",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.show_report = True

    # Step 3: Report Card Output
    if st.session_state.show_report:
        subject_inputs = [
            SubjectInput(
                name=str(r["name"]),
                marks_obtained=float(r["marks"]),
                max_marks=float(r["max_marks"]),
                credits=float(r["credits"]),
            )
            for r in st.session_state.subjects
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

        st.divider()
        st.subheader("3. Official Student Report Card")

        today_str = date.today().strftime("%B %d, %Y")
        st.markdown(_render_report_card_html(summary, today_str), unsafe_allow_html=True)

        # Subject Performance Breakdown Bars
        st.write("")
        with st.expander("📈 Subject Percentage Breakdown", expanded=False):
            for subj in summary.subjects:
                bar_label = (
                    f"**{subj.name}** — {subj.percentage:.2f}% "
                    f"(Grade: **{subj.letter_grade}** | **{subj.status}**)"
                )
                st.markdown(bar_label)
                st.progress(min(max(subj.percentage / 100.0, 0.0), 1.0))

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
