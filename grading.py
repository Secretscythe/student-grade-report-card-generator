"""Core grading calculation and report card generation logic."""

from __future__ import annotations

import csv
import html
import io
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class SubjectInput:
    """Raw input for a single academic subject."""

    name: str
    marks_obtained: float
    max_marks: float = 100.0
    credits: float = 1.0


@dataclass(frozen=True)
class SubjectResult:
    """Calculated grade details for a single academic subject."""

    name: str
    marks_obtained: float
    max_marks: float
    credits: float
    percentage: float
    letter_grade: str
    gpa_points: float
    passed: bool
    status: str


@dataclass(frozen=True)
class ReportCardSummary:
    """Complete calculated academic report card for a student."""

    student_name: str
    student_id: str
    grade_level: str
    term: str
    school_name: str
    subjects: list[SubjectResult]
    total_marks_obtained: float
    total_max_marks: float
    total_credits: float
    overall_percentage: float
    overall_letter_grade: str
    gpa: float
    passed: bool
    status: str
    status_reason: str
    remarks: str


SCALE_STANDARD = "Standard (A, B, C, D, F)"
SCALE_PLUS_MINUS = "Plus/Minus (A+ to F)"


def get_letter_grade_and_gpa(
    percentage: float,
    passing_percentage: float = 60.0,
    scale: str = SCALE_PLUS_MINUS,
) -> tuple[str, float]:
    """Return (letter_grade, gpa_points) for a percentage score.

    Scores strictly below ``passing_percentage`` always receive ``F`` (0.0) so
    the letter grade and pass/fail status remain consistent.
    """
    pct = round(percentage, 2)
    if pct < passing_percentage:
        return ("F", 0.0)

    if scale == SCALE_STANDARD:
        if pct >= 90.0:
            return ("A", 4.0)
        if pct >= 80.0:
            return ("B", 3.0)
        if pct >= 70.0:
            return ("C", 2.0)
        return ("D", 1.0)

    # Plus/Minus scale
    thresholds: list[tuple[float, str, float]] = [
        (97.0, "A+", 4.0),
        (93.0, "A", 4.0),
        (90.0, "A-", 3.7),
        (87.0, "B+", 3.3),
        (83.0, "B", 3.0),
        (80.0, "B-", 2.7),
        (77.0, "C+", 2.3),
        (73.0, "C", 2.0),
        (70.0, "C-", 1.7),
        (67.0, "D+", 1.3),
        (60.0, "D", 1.0),
    ]
    for cutoff, letter, points in thresholds:
        if pct >= cutoff:
            return (letter, points)

    # Passed with a custom passing threshold below 60%
    return ("D-", 1.0)


def get_performance_remarks(overall_percentage: float, passed: bool) -> str:
    """Generate a supportive academic remark based on overall performance."""
    if not passed:
        return "Needs Improvement — Additional review and academic support recommended."
    if overall_percentage >= 93.0:
        return "Outstanding Performance — Exemplary mastery across subjects!"
    if overall_percentage >= 85.0:
        return "Commendable Performance — Strong academic achievement."
    if overall_percentage >= 75.0:
        return "Good Standing — Solid understanding of course material."
    return "Satisfactory — Meets passing requirements; continued effort encouraged."


def validate_subjects(subjects: Sequence[SubjectInput]) -> list[str]:
    """Validate subject inputs and return a list of human-readable errors."""
    errors: list[str] = []
    if not subjects:
        errors.append("Please enter at least one subject to generate a report card.")
        return errors

    for idx, subj in enumerate(subjects, start=1):
        label = subj.name.strip() or f"Row {idx}"
        if not subj.name.strip():
            errors.append(f"Row {idx}: Subject name cannot be empty.")
        if subj.max_marks <= 0:
            errors.append(f"'{label}': Maximum marks must be greater than 0.")
        if subj.marks_obtained < 0:
            errors.append(f"'{label}': Marks obtained cannot be negative.")
        if subj.max_marks > 0 and subj.marks_obtained > subj.max_marks:
            errors.append(
                f"'{label}': Marks obtained ({subj.marks_obtained:g}) cannot exceed "
                f"maximum marks ({subj.max_marks:g})."
            )
        if subj.credits <= 0:
            errors.append(f"'{label}': Credits/weight must be greater than 0.")
    return errors


def calculate_report_card(
    subjects: Sequence[SubjectInput],
    *,
    student_name: str = "Student",
    student_id: str = "N/A",
    grade_level: str = "N/A",
    term: str = "2026–2027 Academic Year",
    school_name: str = "Academic Institution",
    passing_percentage: float = 60.0,
    scale: str = SCALE_PLUS_MINUS,
    require_all_subjects_pass: bool = True,
    use_credit_weights: bool = False,
) -> ReportCardSummary:
    """Calculate per-subject and overall grades, percentage, GPA, and Pass/Fail status."""
    errors = validate_subjects(subjects)
    if errors:
        raise ValueError("; ".join(errors))

    subject_results: list[SubjectResult] = []
    total_obtained = 0.0
    total_max = 0.0
    total_credits = 0.0
    weighted_pct_sum = 0.0
    weighted_gpa_sum = 0.0

    for subj in subjects:
        pct = (subj.marks_obtained / subj.max_marks) * 100.0
        pct_rounded = round(pct, 2)
        subj_passed = pct_rounded >= passing_percentage
        letter, gpa_pts = get_letter_grade_and_gpa(
            pct_rounded,
            passing_percentage=passing_percentage,
            scale=scale,
        )
        subject_results.append(
            SubjectResult(
                name=subj.name.strip(),
                marks_obtained=round(subj.marks_obtained, 2),
                max_marks=round(subj.max_marks, 2),
                credits=round(subj.credits, 2),
                percentage=pct_rounded,
                letter_grade=letter,
                gpa_points=gpa_pts,
                passed=subj_passed,
                status="PASS" if subj_passed else "FAIL",
            )
        )
        total_obtained += subj.marks_obtained
        total_max += subj.max_marks
        weight = subj.credits if use_credit_weights else 1.0
        total_credits += subj.credits
        weighted_pct_sum += pct * weight
        weighted_gpa_sum += gpa_pts * weight

    weight_divisor = sum(s.credits for s in subjects) if use_credit_weights else len(subjects)
    if use_credit_weights:
        overall_pct = round(weighted_pct_sum / weight_divisor, 2)
    else:
        overall_pct = round((total_obtained / total_max) * 100.0, 2)

    gpa = round(weighted_gpa_sum / weight_divisor, 2)

    failed_subjects = [s.name for s in subject_results if not s.passed]
    overall_meets_cutoff = overall_pct >= passing_percentage

    if require_all_subjects_pass:
        passed = overall_meets_cutoff and len(failed_subjects) == 0
    else:
        passed = overall_meets_cutoff

    overall_letter, _ = get_letter_grade_and_gpa(
        overall_pct,
        passing_percentage=passing_percentage,
        scale=scale,
    )

    if passed:
        status_reason = (
            f"Met the {passing_percentage:g}% passing requirement "
            + ("in all subjects." if require_all_subjects_pass else "overall.")
        )
    elif not overall_meets_cutoff and failed_subjects:
        status_reason = (
            f"Overall score ({overall_pct:.2f}%) is below {passing_percentage:g}% "
            f"and failed: {', '.join(failed_subjects)}."
        )
    elif failed_subjects:
        status_reason = (
            f"Overall average is {overall_pct:.2f}%, but failed individual "
            f"subject(s): {', '.join(failed_subjects)}."
        )
    else:
        status_reason = f"Overall score ({overall_pct:.2f}%) is below {passing_percentage:g}%."

    remarks = get_performance_remarks(overall_pct, passed)

    return ReportCardSummary(
        student_name=student_name.strip() or "Student",
        student_id=student_id.strip() or "N/A",
        grade_level=grade_level.strip() or "N/A",
        term=term.strip() or "Current Term",
        school_name=school_name.strip() or "Academic Institution",
        subjects=subject_results,
        total_marks_obtained=round(total_obtained, 2),
        total_max_marks=round(total_max, 2),
        total_credits=round(total_credits, 2),
        overall_percentage=overall_pct,
        overall_letter_grade=overall_letter,
        gpa=gpa,
        passed=passed,
        status="PASS" if passed else "FAIL",
        status_reason=status_reason,
        remarks=remarks,
    )


def export_report_card_csv(summary: ReportCardSummary) -> str:
    """Serialize the calculated report card to CSV text."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Official Student Report Card"])
    writer.writerow(["School / Institution", summary.school_name])
    writer.writerow(["Student Name", summary.student_name])
    writer.writerow(["Student ID", summary.student_id])
    writer.writerow(["Grade / Level", summary.grade_level])
    writer.writerow(["Academic Term", summary.term])
    writer.writerow([])
    writer.writerow(
        [
            "Subject",
            "Marks Obtained",
            "Max Marks",
            "Credits",
            "Percent Grade (%)",
            "Letter Grade",
            "GPA Points",
            "Status",
        ]
    )
    for subj in summary.subjects:
        writer.writerow(
            [
                subj.name,
                f"{subj.marks_obtained:g}",
                f"{subj.max_marks:g}",
                f"{subj.credits:g}",
                f"{subj.percentage:.2f}%",
                subj.letter_grade,
                f"{subj.gpa_points:.1f}",
                subj.status,
            ]
        )
    writer.writerow([])
    writer.writerow(["Total Marks", f"{summary.total_marks_obtained:g} / {summary.total_max_marks:g}"])
    writer.writerow(["Overall Percent Grade", f"{summary.overall_percentage:.2f}%"])
    writer.writerow(["Overall Letter Grade", summary.overall_letter_grade])
    writer.writerow(["Cumulative GPA (4.0)", f"{summary.gpa:.2f}"])
    writer.writerow(["Final Status", summary.status])
    writer.writerow(["Status Details", summary.status_reason])
    writer.writerow(["Remarks", summary.remarks])
    return buffer.getvalue()


def export_report_card_html(summary: ReportCardSummary, generated_date: str) -> str:
    """Generate a standalone, print-friendly HTML report card."""
    badge_bg = "#dcfce7" if summary.passed else "#fee2e2"
    badge_fg = "#166534" if summary.passed else "#991b1b"
    badge_border = "#86efac" if summary.passed else "#fca5a5"

    rows_html = []
    for s in summary.subjects:
        s_bg = "#dcfce7" if s.passed else "#fee2e2"
        s_fg = "#166534" if s.passed else "#991b1b"
        rows_html.append(
            f"""
            <tr>
                <td>{html.escape(s.name)}</td>
                <td class="num">{s.marks_obtained:g} / {s.max_marks:g}</td>
                <td class="num">{s.credits:g}</td>
                <td class="num"><strong>{s.percentage:.2f}%</strong></td>
                <td class="center"><strong>{html.escape(s.letter_grade)}</strong></td>
                <td class="center">
                    <span class="pill" style="background:{s_bg};color:{s_fg};">
                        {html.escape(s.status)}
                    </span>
                </td>
            </tr>
            """
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Report Card - {html.escape(summary.student_name)}</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f8fafc;
    color: #0f172a;
    margin: 0;
    padding: 32px 16px;
  }}
  .card {{
    max-width: 820px;
    margin: 0 auto;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 36px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  }}
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 2px solid #1e3a8a;
    padding-bottom: 18px;
    margin-bottom: 24px;
  }}
  .school {{
    font-size: 24px;
    font-weight: 800;
    color: #1e3a8a;
    margin: 0 0 4px 0;
  }}
  .subtitle {{
    font-size: 14px;
    color: #64748b;
    margin: 0;
  }}
  .status-badge {{
    padding: 10px 20px;
    border-radius: 999px;
    font-weight: 800;
    font-size: 16px;
    letter-spacing: 0.05em;
    background: {badge_bg};
    color: {badge_fg};
    border: 1px solid {badge_border};
  }}
  .meta-grid {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px 24px;
    background: #f8fafc;
    padding: 16px 20px;
    border-radius: 10px;
    margin-bottom: 24px;
    font-size: 14px;
  }}
  .meta-label {{
    color: #64748b;
    font-weight: 600;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 24px;
    font-size: 14px;
  }}
  th {{
    background: #1e3a8a;
    color: #ffffff;
    text-align: left;
    padding: 12px;
    font-weight: 600;
  }}
  td {{
    padding: 12px;
    border-bottom: 1px solid #e2e8f0;
  }}
  .num {{ text-align: right; }}
  .center {{ text-align: center; }}
  .pill {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
  }}
  .summary-grid {{
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
    margin-bottom: 20px;
  }}
  .metric {{
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px;
    text-align: center;
    background: #f8fafc;
  }}
  .metric-label {{
    font-size: 12px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 6px;
  }}
  .metric-value {{
    font-size: 22px;
    font-weight: 800;
    color: #0f172a;
  }}
  .remarks {{
    border-left: 4px solid #1e3a8a;
    background: #eff6ff;
    padding: 14px 18px;
    border-radius: 0 8px 8px 0;
    font-size: 14px;
  }}
  @media print {{
    body {{ background: #ffffff; padding: 0; }}
    .card {{ box-shadow: none; border: none; padding: 12px; }}
  }}
</style>
</head>
<body>
  <div class="card">
    <div class="header">
      <div>
        <h1 class="school">{html.escape(summary.school_name)}</h1>
        <p class="subtitle">Official Student Academic Report Card &bull; Generated {html.escape(generated_date)}</p>
      </div>
      <div class="status-badge">FINAL STATUS: {html.escape(summary.status)}</div>
    </div>

    <div class="meta-grid">
      <div><span class="meta-label">Student Name:</span> {html.escape(summary.student_name)}</div>
      <div><span class="meta-label">Student ID:</span> {html.escape(summary.student_id)}</div>
      <div><span class="meta-label">Grade / Year:</span> {html.escape(summary.grade_level)}</div>
      <div><span class="meta-label">Academic Term:</span> {html.escape(summary.term)}</div>
    </div>

    <table>
      <thead>
        <tr>
          <th>Subject</th>
          <th class="num">Marks</th>
          <th class="num">Credits</th>
          <th class="num">Percent Grade</th>
          <th class="center">Letter Grade</th>
          <th class="center">Status</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows_html)}
      </tbody>
    </table>

    <div class="summary-grid">
      <div class="metric">
        <div class="metric-label">Total Marks</div>
        <div class="metric-value">{summary.total_marks_obtained:g} / {summary.total_max_marks:g}</div>
      </div>
      <div class="metric">
        <div class="metric-label">Percent Grade</div>
        <div class="metric-value">{summary.overall_percentage:.2f}%</div>
      </div>
      <div class="metric">
        <div class="metric-label">Letter Grade</div>
        <div class="metric-value">{html.escape(summary.overall_letter_grade)}</div>
      </div>
      <div class="metric">
        <div class="metric-label">GPA (4.0)</div>
        <div class="metric-value">{summary.gpa:.2f}</div>
      </div>
    </div>

    <div class="remarks">
      <strong>Status Summary:</strong> {html.escape(summary.status_reason)}<br>
      <strong>Advisor Remarks:</strong> {html.escape(summary.remarks)}
    </div>
  </div>
</body>
</html>
"""
