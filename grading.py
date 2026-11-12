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


def get_grade_tier_colors(letter_grade: str) -> tuple[str, str, str]:
    """Return (bg_color, text_color, bar_color) for a letter grade."""
    grade_upper = letter_grade.strip().upper()
    if grade_upper.startswith("A"):
        return ("#ecfdf5", "#047857", "#10b981")
    if grade_upper.startswith("B"):
        return ("#eff6ff", "#1d4ed8", "#3b82f6")
    if grade_upper.startswith("C"):
        return ("#fffbeb", "#b45309", "#f59e0b")
    if grade_upper.startswith("D"):
        return ("#fff7ed", "#c2410c", "#f97316")
    return ("#fef2f2", "#b91c1c", "#ef4444")


def get_honor_standing(gpa: float, passed: bool) -> str:
    """Return an academic standing badge label based on GPA and pass status."""
    if not passed:
        return "Academic Review Required"
    if gpa >= 3.85:
        return "Highest Honors"
    if gpa >= 3.50:
        return "Dean's Honor List"
    if gpa >= 3.00:
        return "Honor Roll"
    return "Good Standing"


def export_report_card_html(summary: ReportCardSummary, generated_date: str) -> str:
    """Generate a standalone, print-friendly HTML report card."""
    badge_bg = "#ecfdf5" if summary.passed else "#fef2f2"
    badge_fg = "#065f46" if summary.passed else "#991b1b"
    badge_border = "#6ee7b7" if summary.passed else "#fca5a5"
    status_icon = "&#10003;" if summary.passed else "&#10005;"
    standing_label = get_honor_standing(summary.gpa, summary.passed)
    overall_bg, overall_fg, _ = get_grade_tier_colors(summary.overall_letter_grade)

    rows_html = []
    for s in summary.subjects:
        s_bg = "#dcfce7" if s.passed else "#fee2e2"
        s_fg = "#166534" if s.passed else "#991b1b"
        g_bg, g_fg, g_bar = get_grade_tier_colors(s.letter_grade)
        bar_width = min(max(s.percentage, 0.0), 100.0)
        s_icon = "&#10003;" if s.passed else "&#10005;"
        rows_html.append(
            f"""
            <tr>
                <td><strong style="color:#0f172a;">{html.escape(s.name)}</strong></td>
                <td class="num">{s.marks_obtained:g} <span style="color:#94a3b8;">/ {s.max_marks:g}</span></td>
                <td class="num">{s.credits:g}</td>
                <td class="pct-cell">
                    <div class="pct-wrap">
                        <span class="pct-val">{s.percentage:.2f}%</span>
                        <div class="pct-track"><div class="pct-fill" style="width:{bar_width:.1f}%;background:{g_bar};"></div></div>
                    </div>
                </td>
                <td class="center">
                    <span class="grade-chip" style="background:{g_bg};color:{g_fg};">{html.escape(s.letter_grade)}</span>
                </td>
                <td class="num">{s.gpa_points:.1f}</td>
                <td class="center">
                    <span class="pill" style="background:{s_bg};color:{s_fg};">
                        {s_icon} {html.escape(s.status)}
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
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');
  * {{ box-sizing: border-box; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f1f5f9;
    color: #0f172a;
    margin: 0;
    padding: 36px 16px;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  .card {{
    max-width: 880px;
    margin: 0 auto;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 20px 40px -15px rgba(15, 23, 42, 0.10);
  }}
  .top-accent {{
    height: 8px;
    background: linear-gradient(90deg, #1e3a8a 0%, #2563eb 50%, #4f46e5 100%);
  }}
  .card-inner {{
    padding: 36px 40px;
  }}
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 22px;
    margin-bottom: 24px;
  }}
  .brand-wrap {{
    display: flex;
    align-items: center;
    gap: 14px;
  }}
  .crest {{
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: linear-gradient(135deg, #1e3a8a, #3b82f6);
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    flex-shrink: 0;
  }}
  .school {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 23px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.02em;
    margin: 0 0 4px 0;
  }}
  .subtitle {{
    font-size: 13px;
    color: #64748b;
    margin: 0;
    font-weight: 500;
  }}
  .badge-stack {{
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 6px;
  }}
  .status-badge {{
    padding: 8px 18px;
    border-radius: 999px;
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 0.05em;
    background: {badge_bg};
    color: {badge_fg};
    border: 1.5px solid {badge_border};
  }}
  .standing-tag {{
    font-size: 12px;
    font-weight: 600;
    color: #475569;
    background: #f1f5f9;
    padding: 4px 12px;
    border-radius: 999px;
  }}
  .meta-grid {{
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    padding: 16px 20px;
    border-radius: 12px;
    margin-bottom: 24px;
  }}
  .meta-item {{
    display: flex;
    flex-direction: column;
    gap: 3px;
  }}
  .meta-label {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #64748b;
    font-weight: 700;
  }}
  .meta-val {{
    font-size: 14px;
    font-weight: 700;
    color: #0f172a;
  }}
  .summary-grid {{
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
    margin-bottom: 26px;
  }}
  .metric {{
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    background: #ffffff;
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.03);
  }}
  .metric-label {{
    font-size: 11px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 700;
    margin-bottom: 8px;
  }}
  .metric-value {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 24px;
    font-weight: 800;
    color: #0f172a;
  }}
  .metric-sub {{
    font-size: 12px;
    color: #64748b;
    margin-top: 4px;
    font-weight: 500;
  }}
  table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    margin-bottom: 24px;
    font-size: 13.5px;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    overflow: hidden;
  }}
  th {{
    background: #0f172a;
    color: #f8fafc;
    text-align: left;
    padding: 12px 14px;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  td {{
    padding: 12px 14px;
    border-bottom: 1px solid #e2e8f0;
    color: #334155;
  }}
  tbody tr:nth-child(even) {{ background: #f8fafc; }}
  tfoot td {{
    background: #f1f5f9;
    font-weight: 700;
    color: #0f172a;
    border-bottom: none;
    border-top: 2px solid #cbd5e1;
  }}
  .num {{ text-align: right; }}
  .center {{ text-align: center; }}
  .pct-cell {{ width: 170px; }}
  .pct-wrap {{ display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }}
  .pct-val {{ font-weight: 700; color: #0f172a; }}
  .pct-track {{ width: 100%; height: 6px; background: #e2e8f0; border-radius: 999px; overflow: hidden; }}
  .pct-fill {{ height: 100%; border-radius: 999px; }}
  .grade-chip {{
    display: inline-block;
    min-width: 36px;
    padding: 3px 10px;
    border-radius: 8px;
    font-weight: 800;
    font-size: 13px;
  }}
  .pill {{
    display: inline-block;
    padding: 4px 11px;
    border-radius: 999px;
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.03em;
  }}
  .remarks {{
    border: 1px solid #bfdbfe;
    border-left: 5px solid #2563eb;
    background: #eff6ff;
    padding: 16px 20px;
    border-radius: 10px;
    font-size: 13.5px;
    line-height: 1.6;
    color: #1e293b;
    margin-bottom: 28px;
  }}
  .signatures {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 48px;
    padding-top: 20px;
    margin-top: 12px;
  }}
  .sig-line {{
    border-top: 1px solid #94a3b8;
    padding-top: 8px;
    font-size: 12px;
    color: #64748b;
    font-weight: 600;
  }}
  @media print {{
    body {{ background: #ffffff; padding: 0; }}
    .card {{ box-shadow: none; border: 1px solid #cbd5e1; }}
  }}
</style>
</head>
<body>
  <div class="card">
    <div class="top-accent"></div>
    <div class="card-inner">
      <div class="header">
        <div class="brand-wrap">
          <div class="crest">&#127891;</div>
          <div>
            <h1 class="school">{html.escape(summary.school_name)}</h1>
            <p class="subtitle">Official Student Academic Transcript &amp; Report Card &bull; Issued {html.escape(generated_date)}</p>
          </div>
        </div>
        <div class="badge-stack">
          <div class="status-badge">{status_icon} FINAL STATUS: {html.escape(summary.status)}</div>
          <div class="standing-tag">{html.escape(standing_label)}</div>
        </div>
      </div>

      <div class="meta-grid">
        <div class="meta-item"><span class="meta-label">Student Name</span><span class="meta-val">{html.escape(summary.student_name)}</span></div>
        <div class="meta-item"><span class="meta-label">Student ID</span><span class="meta-val">{html.escape(summary.student_id)}</span></div>
        <div class="meta-item"><span class="meta-label">Grade / Level</span><span class="meta-val">{html.escape(summary.grade_level)}</span></div>
        <div class="meta-item"><span class="meta-label">Academic Term</span><span class="meta-val">{html.escape(summary.term)}</span></div>
      </div>

      <div class="summary-grid">
        <div class="metric">
          <div class="metric-label">Overall Percentage</div>
          <div class="metric-value">{summary.overall_percentage:.2f}%</div>
          <div class="metric-sub">{summary.total_marks_obtained:g} / {summary.total_max_marks:g} Marks</div>
        </div>
        <div class="metric" style="background:{overall_bg};">
          <div class="metric-label">Letter Grade</div>
          <div class="metric-value" style="color:{overall_fg};">{html.escape(summary.overall_letter_grade)}</div>
          <div class="metric-sub">{html.escape(standing_label)}</div>
        </div>
        <div class="metric">
          <div class="metric-label">Cumulative GPA</div>
          <div class="metric-value">{summary.gpa:.2f}</div>
          <div class="metric-sub">4.00 Unweighted Scale</div>
        </div>
        <div class="metric">
          <div class="metric-label">Academic Standing</div>
          <div class="metric-value" style="color:{badge_fg};">{html.escape(summary.status)}</div>
          <div class="metric-sub">{summary.total_credits:g} Total Credits</div>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th>Course / Subject</th>
            <th class="num">Marks</th>
            <th class="num">Credits</th>
            <th class="num">Percentage</th>
            <th class="center">Grade</th>
            <th class="num">GPA Pts</th>
            <th class="center">Standing</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows_html)}
        </tbody>
        <tfoot>
          <tr>
            <td>Cumulative Summary ({len(summary.subjects)} Courses)</td>
            <td class="num">{summary.total_marks_obtained:g} / {summary.total_max_marks:g}</td>
            <td class="num">{summary.total_credits:g}</td>
            <td class="num">{summary.overall_percentage:.2f}%</td>
            <td class="center">{html.escape(summary.overall_letter_grade)}</td>
            <td class="num">{summary.gpa:.2f}</td>
            <td class="center">{html.escape(summary.status)}</td>
          </tr>
        </tfoot>
      </table>

      <div class="remarks">
        <strong>Determination:</strong> {html.escape(summary.status_reason)}<br>
        <strong>Academic Advisor Remarks:</strong> {html.escape(summary.remarks)}
      </div>

      <div class="signatures">
        <div class="sig-line"> Academic Advisor / Homeroom Signature</div>
        <div class="sig-line"> Office of the Registrar &bull; Official Seal</div>
      </div>
    </div>
  </div>
</body>
</html>
"""

