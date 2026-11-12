"""Unit tests for Student Grade & Report Card Generator."""

from __future__ import annotations

import unittest

from grading import (
    SCALE_PLUS_MINUS,
    SCALE_STANDARD,
    SubjectInput,
    calculate_report_card,
    export_report_card_csv,
    export_report_card_html,
    get_grade_tier_colors,
    get_honor_standing,
    get_letter_grade_and_gpa,
    validate_subjects,
)


class TestGradingCalculations(unittest.TestCase):
    def test_letter_grades_plus_minus_scale(self) -> None:
        self.assertEqual(get_letter_grade_and_gpa(98.5), ("A+", 4.0))
        self.assertEqual(get_letter_grade_and_gpa(94.0), ("A", 4.0))
        self.assertEqual(get_letter_grade_and_gpa(90.0), ("A-", 3.7))
        self.assertEqual(get_letter_grade_and_gpa(88.0), ("B+", 3.3))
        self.assertEqual(get_letter_grade_and_gpa(75.0), ("C", 2.0))
        self.assertEqual(get_letter_grade_and_gpa(59.9), ("F", 0.0))

    def test_letter_grades_standard_scale(self) -> None:
        self.assertEqual(get_letter_grade_and_gpa(92.0, scale=SCALE_STANDARD), ("A", 4.0))
        self.assertEqual(get_letter_grade_and_gpa(85.0, scale=SCALE_STANDARD), ("B", 3.0))
        self.assertEqual(get_letter_grade_and_gpa(72.0, scale=SCALE_STANDARD), ("C", 2.0))
        self.assertEqual(get_letter_grade_and_gpa(61.0, scale=SCALE_STANDARD), ("D", 1.0))
        self.assertEqual(get_letter_grade_and_gpa(45.0, scale=SCALE_STANDARD), ("F", 0.0))

    def test_passing_report_card(self) -> None:
        subjects = [
            SubjectInput("Mathematics", 92, 100),
            SubjectInput("Science", 86, 100),
            SubjectInput("English", 88, 100),
            SubjectInput("History", 79, 100),
            SubjectInput("Computer Science", 95, 100),
        ]
        summary = calculate_report_card(
            subjects,
            student_name="Alex Johnson",
            student_id="STU-104",
            passing_percentage=60.0,
            scale=SCALE_PLUS_MINUS,
        )
        self.assertEqual(summary.total_marks_obtained, 440.0)
        self.assertEqual(summary.total_max_marks, 500.0)
        self.assertEqual(summary.overall_percentage, 88.0)
        self.assertEqual(summary.overall_letter_grade, "B+")
        self.assertTrue(summary.passed)
        self.assertEqual(summary.status, "PASS")
        self.assertTrue(all(s.status == "PASS" for s in summary.subjects))

    def test_failing_due_to_individual_subject(self) -> None:
        subjects = [
            SubjectInput("Mathematics", 95, 100),
            SubjectInput("Physics", 45, 100),
            SubjectInput("Chemistry", 90, 100),
        ]
        summary_strict = calculate_report_card(
            subjects,
            passing_percentage=60.0,
            require_all_subjects_pass=True,
        )
        self.assertAlmostEqual(summary_strict.overall_percentage, 76.67, places=2)
        self.assertFalse(summary_strict.passed)
        self.assertEqual(summary_strict.status, "FAIL")
        self.assertIn("Physics", summary_strict.status_reason)

        summary_overall_only = calculate_report_card(
            subjects,
            passing_percentage=60.0,
            require_all_subjects_pass=False,
        )
        self.assertTrue(summary_overall_only.passed)
        self.assertEqual(summary_overall_only.status, "PASS")

    def test_credit_weighted_calculation(self) -> None:
        subjects = [
            SubjectInput("Major Project", 95, 100, credits=4.0),
            SubjectInput("Seminar", 70, 100, credits=1.0),
        ]
        summary = calculate_report_card(subjects, use_credit_weights=True)
        # (95*4 + 70*1) / 5 = 90.0%
        self.assertEqual(summary.overall_percentage, 90.0)
        self.assertEqual(summary.overall_letter_grade, "A-")

    def test_validation_catches_invalid_marks(self) -> None:
        errors = validate_subjects(
            [
                SubjectInput("", 80, 100),
                SubjectInput("Math", 110, 100),
                SubjectInput("Science", -5, 100),
            ]
        )
        self.assertEqual(len(errors), 3)

    def test_csv_and_html_exports(self) -> None:
        subjects = [SubjectInput("Biology", 84, 100)]
        summary = calculate_report_card(subjects, student_name="Sam Rivera")
        csv_text = export_report_card_csv(summary)
        html_text = export_report_card_html(summary, "November 05, 2026")

        self.assertIn("Sam Rivera", csv_text)
        self.assertIn("84.00%", csv_text)
        self.assertIn("PASS", csv_text)
        self.assertIn("Sam Rivera", html_text)
        self.assertIn("FINAL STATUS: PASS", html_text)

    def test_grade_tier_colors_and_honor_standing(self) -> None:
        self.assertEqual(get_grade_tier_colors("A+")[1], "#047857")
        self.assertEqual(get_grade_tier_colors("B")[1], "#1d4ed8")
        self.assertEqual(get_grade_tier_colors("C-")[1], "#b45309")
        self.assertEqual(get_grade_tier_colors("D")[1], "#c2410c")
        self.assertEqual(get_grade_tier_colors("F")[1], "#b91c1c")

        self.assertEqual(get_honor_standing(3.9, True), "Highest Honors")
        self.assertEqual(get_honor_standing(3.6, True), "Dean's Honor List")
        self.assertEqual(get_honor_standing(3.2, True), "Honor Roll")
        self.assertEqual(get_honor_standing(2.5, True), "Good Standing")
        self.assertEqual(get_honor_standing(3.5, False), "Academic Review Required")

    def test_app_smoke_execution_with_mocked_streamlit(self) -> None:
        """Verify app.py imports and executes main() cleanly."""
        import importlib
        import sys
        import types

        class _DummyContext:
            def __enter__(self) -> "_DummyContext":
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def markdown(self, *args: object, **kwargs: object) -> None:
                return None

        class _SessionState(dict):
            def __getattr__(self, key: str) -> object:
                return self[key]

            def __setattr__(self, key: str, value: object) -> None:
                self[key] = value

        fake_st = types.ModuleType("streamlit")
        fake_st.session_state = _SessionState()  # type: ignore[attr-defined]
        fake_st.set_page_config = lambda **kwargs: None  # type: ignore[attr-defined]
        fake_st.markdown = lambda *a, **kw: None  # type: ignore[attr-defined]
        fake_st.header = lambda *a, **kw: None  # type: ignore[attr-defined]
        fake_st.subheader = lambda *a, **kw: None  # type: ignore[attr-defined]
        fake_st.caption = lambda *a, **kw: None  # type: ignore[attr-defined]
        fake_st.divider = lambda *a, **kw: None  # type: ignore[attr-defined]
        fake_st.write = lambda *a, **kw: None  # type: ignore[attr-defined]
        fake_st.progress = lambda *a, **kw: None  # type: ignore[attr-defined]
        fake_st.error = lambda *a, **kw: None  # type: ignore[attr-defined]
        fake_st.warning = lambda *a, **kw: None  # type: ignore[attr-defined]
        fake_st.rerun = lambda: None  # type: ignore[attr-defined]
        fake_st.sidebar = _DummyContext()  # type: ignore[attr-defined]
        fake_st.expander = lambda *a, **kw: _DummyContext()  # type: ignore[attr-defined]
        fake_st.columns = lambda spec: [  # type: ignore[attr-defined]
            _DummyContext() for _ in range(spec if isinstance(spec, int) else len(spec))
        ]
        fake_st.selectbox = lambda label, options, index=0, **kw: options[index]  # type: ignore[attr-defined]
        fake_st.slider = lambda label, value=60, **kw: value  # type: ignore[attr-defined]
        fake_st.checkbox = lambda label, value=False, **kw: value  # type: ignore[attr-defined]
        fake_st.text_input = lambda label, value="", **kw: value  # type: ignore[attr-defined]
        fake_st.number_input = lambda label, value=0.0, **kw: value  # type: ignore[attr-defined]
        fake_st.file_uploader = lambda *a, **kw: None  # type: ignore[attr-defined]
        fake_st.download_button = lambda *a, **kw: False  # type: ignore[attr-defined]
        fake_st.button = (  # type: ignore[attr-defined]
            lambda label, **kw: "Generate Report Card" in str(label)
        )

        had_st = "streamlit" in sys.modules
        orig_st = sys.modules.get("streamlit")
        sys.modules["streamlit"] = fake_st
        try:
            app_mod = importlib.import_module("app")
            app_mod.main()
            self.assertTrue(fake_st.session_state["show_report"])
            rows = app_mod._parse_uploaded_csv("Subject,Marks,Max Marks\nBiology,91,100\n")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["name"], "Biology")
        finally:
            sys.modules.pop("app", None)
            if had_st and orig_st is not None:
                sys.modules["streamlit"] = orig_st
            else:
                sys.modules.pop("streamlit", None)


if __name__ == "__main__":
    unittest.main()
