"""Authentication, role-based access control, and user management."""

from __future__ import annotations

import base64
import hashlib
import hmac
import html
import json
import os
import random
import secrets
import urllib.error
import urllib.request
from dataclasses import dataclass, replace

_DEFAULT_RESEND_B64 = "cmVfUEY5bmVFaHlfUFJrMXVCQzUyU01rdWJCYW5VeW9hcDZ0"


def get_configured_resend_api_key(explicit_key: str = "") -> str:
    """Resolve the Resend API key from argument, environment, or configured default."""
    if explicit_key.strip():
        return explicit_key.strip()
    env_key = os.environ.get("RESEND_API_KEY", "").strip()
    if env_key:
        return env_key
    return base64.b64decode(_DEFAULT_RESEND_B64).decode("utf-8")

ROLE_STUDENT = "Student"
ROLE_TEACHER = "Teacher"
ROLE_ADMIN = "Administrator"
VALID_ROLES = (ROLE_STUDENT, ROLE_TEACHER, ROLE_ADMIN)
DEMO_STUDENT_USERNAMES = ("alex", "sam", "priya")

CORE_SUBJECTS: tuple[str, ...] = ("History", "Science", "Math", "English")
ELECTIVE_OPTIONS: tuple[str, ...] = (
    "Computer Science",
    "Art & Design",
    "Spanish",
    "Music",
    "Physical Education",
    "Economics",
    "Psychology",
    "Robotics",
    "Drama & Theater",
    "Business Studies",
)
ALL_SUBJECT_OPTIONS: tuple[str, ...] = (*CORE_SUBJECTS, *ELECTIVE_OPTIONS)


def get_student_subject_names(
    elective_1: str = "Computer Science",
    elective_2: str = "Art & Design",
) -> list[str]:
    """Return the 4 required core subjects plus the student's 2 chosen electives."""
    e1 = elective_1.strip() or "Computer Science"
    e2 = elective_2.strip() or "Art & Design"
    if e2.lower() == e1.lower():
        e2 = f"{e2} II"
    return [*CORE_SUBJECTS, e1, e2]


def build_empty_student_subjects(
    elective_1: str = "Computer Science",
    elective_2: str = "Art & Design",
) -> list[dict[str, object]]:
    """Build the 6 subject rows (History, Science, Math, English + 2 Electives) starting at 100."""
    subject_names = get_student_subject_names(elective_1, elective_2)
    return [
        {
            "id": idx,
            "name": subj_name,
            "marks": 100.0,
            "max_marks": 100.0,
            "credits": 1.0,
            "assignments": [],
        }
        for idx, subj_name in enumerate(subject_names, start=1)
    ]


def generate_random_demo_assignments(
    count: int = 6,
    electives: tuple[str, str] = ("Computer Science", "Art & Design"),
) -> list[dict[str, object]]:
    """Generate the 6 subjects (History, Science, Math, English + 2 electives) with random assignments for demo logins."""
    subject_names = get_student_subject_names(electives[0], electives[1])
    task_types = ("Homework Assignment", "Unit Quiz", "Midterm Test", "Project / Lab")
    rows: list[dict[str, object]] = []
    for idx, subj_name in enumerate(subject_names[:count], start=1):
        chosen_tasks = random.sample(task_types, k=3)
        subj_assignments = []
        for a_idx, t_label in enumerate(chosen_tasks, start=1):
            score = float(random.randint(62, 99))
            subj_assignments.append(
                {
                    "id": idx * 100 + a_idx,
                    "title": f"{subj_name} — {t_label}",
                    "score": score,
                }
            )
        avg_score = round(
            sum(float(a["score"]) for a in subj_assignments) / len(subj_assignments),
            2,
        )
        rows.append(
            {
                "id": idx,
                "name": subj_name,
                "marks": avg_score,
                "max_marks": 100.0,
                "credits": 1.0,
                "assignments": subj_assignments,
            }
        )
    return rows

DEFAULT_SCHOOL = "Westview Academy of Arts & Sciences"
DEFAULT_SCHOOLS = (
    "Westview Academy of Arts & Sciences",
    "Oakridge International High School",
    "Northstar STEM Preparatory",
)


@dataclass(frozen=True)
class UserAccount:
    """Represents an authenticated Student, Teacher, or Administrator account."""

    username: str
    full_name: str
    role: str
    student_id: str
    grade_level: str
    password_salt: str
    password_hash: str
    school_name: str = DEFAULT_SCHOOL
    electives: tuple[str, str] = ("Computer Science", "Art & Design")
    email: str = ""
    teaching_subject: str = "Math"


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Return (salt_hex, hash_hex) for a password using PBKDF2-HMAC-SHA256."""
    use_salt = salt or secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        use_salt.encode("utf-8"),
        100_000,
    ).hex()
    return (use_salt, derived)


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 salt and hash."""
    _, computed_hash = hash_password(password, salt=salt)
    return hmac.compare_digest(computed_hash, expected_hash)


def _make_user(
    username: str,
    password: str,
    full_name: str,
    role: str,
    student_id: str,
    grade_level: str,
    fixed_salt: str,
    school_name: str = DEFAULT_SCHOOL,
    email: str = "",
    teaching_subject: str = "Math",
) -> UserAccount:
    salt, pwd_hash = hash_password(password, salt=fixed_salt)
    return UserAccount(
        username=username.lower(),
        full_name=full_name,
        role=role,
        student_id=student_id,
        grade_level=grade_level,
        password_salt=salt,
        password_hash=pwd_hash,
        school_name=school_name,
        email=email or f"{username.lower()}@westview.edu",
        teaching_subject=teaching_subject,
    )


def generate_student_id(existing_ids: set[str] | None = None) -> str:
    """Generate a unique 8-digit numeric Student ID."""
    taken = existing_ids or set()
    for _ in range(100):
        candidate = f"{secrets.randbelow(90_000_000) + 10_000_000}"
        if candidate not in taken:
            return candidate
    return f"{secrets.randbelow(90_000_000) + 10_000_000}"


def get_default_users() -> dict[str, UserAccount]:
    """Return pre-seeded demo accounts for Student, Teacher, and Administrator."""
    accounts = [
        _make_user(
            username="alex",
            password="student123",
            full_name="Alex Johnson",
            role=ROLE_STUDENT,
            student_id="20260104",
            grade_level="Grade 11",
            fixed_salt="a1b2c3d4e5f60718293a4b5c6d7e8f90",
        ),
        _make_user(
            username="sam",
            password="student123",
            full_name="Sam Rivera",
            role=ROLE_STUDENT,
            student_id="20260209",
            grade_level="Grade 12",
            fixed_salt="f0e9d8c7b6a594837261504f3e2d1c0b",
        ),
        _make_user(
            username="priya",
            password="student123",
            full_name="Priya Patel",
            role=ROLE_STUDENT,
            student_id="20260315",
            grade_level="Grade 11",
            fixed_salt="99887766554433221100ffeeddccbbaa",
        ),
        _make_user(
            username="teacher",
            password="teacher123",
            full_name="Prof. Sarah Jenkins",
            role=ROLE_TEACHER,
            student_id="10020261",
            grade_level="Senior Faculty",
            fixed_salt="11223344556677889900aabbccddeeff",
            teaching_subject="Math",
        ),
        _make_user(
            username="mr_kim",
            password="teacher123",
            full_name="Mr. David Kim",
            role=ROLE_TEACHER,
            student_id="10020262",
            grade_level="Faculty",
            fixed_salt="22334455667788990011aabbccddeeff",
            teaching_subject="Science",
        ),
        _make_user(
            username="ms_elena",
            password="teacher123",
            full_name="Ms. Elena Rostova",
            role=ROLE_TEACHER,
            student_id="10020263",
            grade_level="Faculty",
            fixed_salt="33445566778899001122aabbccddeeff",
            teaching_subject="English",
        ),
        _make_user(
            username="admin",
            password="admin123",
            full_name="Dr. Marcus Sterling",
            role=ROLE_ADMIN,
            student_id="10020260",
            grade_level="Principal & Registrar",
            fixed_salt="abcdef0123456789abcdef0123456789",
        ),
    ]
    return {acct.username: acct for acct in accounts}


def get_default_student_roster() -> dict[str, dict[str, object]]:
    """Return initial multi-student academic records for Demo views."""
    return {
        "20260104": {
            "student_name": "Alex Johnson",
            "student_id": "20260104",
            "grade_level": "Grade 11",
            "school_name": DEFAULT_SCHOOL,
            "username": "alex",
            "electives": ["Computer Science", "Art & Design"],
            "is_demo": True,
            "custom_remarks": "",
            "subjects": generate_random_demo_assignments(6, ("Computer Science", "Art & Design")),
        },
        "20260209": {
            "student_name": "Sam Rivera",
            "student_id": "20260209",
            "grade_level": "Grade 12",
            "school_name": DEFAULT_SCHOOL,
            "username": "sam",
            "electives": ["Economics", "Spanish"],
            "is_demo": True,
            "custom_remarks": "",
            "subjects": generate_random_demo_assignments(6, ("Economics", "Spanish")),
        },
        "20260315": {
            "student_name": "Priya Patel",
            "student_id": "20260315",
            "grade_level": "Grade 11",
            "school_name": DEFAULT_SCHOOL,
            "username": "priya",
            "electives": ["Robotics", "Music"],
            "is_demo": True,
            "custom_remarks": "Scheduled for weekly Mathematics tutoring session.",
            "subjects": generate_random_demo_assignments(6, ("Robotics", "Music")),
        },
    }


def authenticate_user(
    users: dict[str, UserAccount],
    username: str,
    password: str,
) -> UserAccount | None:
    """Validate credentials and return the matching UserAccount if valid."""
    key = username.strip().lower()
    if not key or not password:
        return None
    account = users.get(key)
    if account is None:
        return None
    if verify_password(password, account.password_salt, account.password_hash):
        return account
    return None


def register_user(
    users: dict[str, UserAccount],
    *,
    username: str,
    password: str,
    full_name: str,
    role: str = ROLE_STUDENT,
    student_id: str = "",
    grade_level: str = "Grade 11",
    school_name: str = DEFAULT_SCHOOL,
    electives: tuple[str, str] = ("Computer Science", "Art & Design"),
    email: str = "",
    teaching_subject: str = "Math",
) -> tuple[UserAccount | None, str | None]:
    """Register a new Student, Teacher, or Administrator account.

    Returns (UserAccount, None) on success or (None, error_message) on failure.
    """
    clean_user = username.strip().lower()
    clean_name = full_name.strip()
    existing_ids = {u.student_id for u in users.values()}
    clean_id = student_id.strip() or generate_student_id(existing_ids)
    clean_grade = grade_level.strip() or "Grade 11"
    clean_school = school_name.strip() or DEFAULT_SCHOOL
    clean_email = email.strip().lower()
    clean_subj = teaching_subject.strip() or "Math"

    if len(clean_user) < 3:
        return (None, "Username must be at least 3 characters long.")
    if not all(c.isalnum() or c in "_.-" for c in clean_user):
        return (None, "Username may only contain letters, numbers, '.', '_', or '-'.")
    if clean_user in users:
        return (None, f"Username '{clean_user}' is already registered.")
    if not clean_name:
        return (None, "Full name cannot be empty.")
    if len(password) < 6:
        return (None, "Password must be at least 6 characters long.")
    if clean_email and "@" not in clean_email:
        return (None, "Please enter a valid email address.")

    normalized_role = role if role in VALID_ROLES else ROLE_STUDENT
    salt, pwd_hash = hash_password(password)
    new_account = UserAccount(
        username=clean_user,
        full_name=clean_name,
        role=normalized_role,
        student_id=clean_id,
        grade_level=clean_grade,
        password_salt=salt,
        password_hash=pwd_hash,
        school_name=clean_school,
        electives=electives,
        email=clean_email or f"{clean_user}@westview.edu",
        teaching_subject=clean_subj,
    )
    users[clean_user] = new_account
    return (new_account, None)


def delete_user_account(
    users: dict[str, UserAccount],
    target_username: str,
    acting_username: str,
) -> tuple[bool, str]:
    """Delete a user account (Admin action). Cannot delete own active account."""
    key = target_username.strip().lower()
    if key == acting_username.strip().lower():
        return (False, "You cannot delete your own currently signed-in administrator account.")
    if key not in users:
        return (False, f"User '{target_username}' not found.")
    del users[key]
    return (True, f"Removed account '{key}'.")


def find_user_by_username_or_email(
    users: dict[str, UserAccount],
    identifier: str,
) -> UserAccount | None:
    """Find a user account by username or recovery email address."""
    query = identifier.strip().lower()
    if not query:
        return None
    if query in users:
        return users[query]
    for acct in users.values():
        if acct.email.strip().lower() == query:
            return acct
    return None


def generate_recovery_code() -> str:
    """Generate a cryptographically random 6-digit numeric recovery code."""
    return f"{secrets.randbelow(900000) + 100000}"


def reset_user_password(
    users: dict[str, UserAccount],
    username: str,
    new_password: str,
) -> tuple[bool, str]:
    """Reset the password for an existing user account."""
    key = username.strip().lower()
    if key not in users:
        return (False, "Account not found.")
    if len(new_password) < 6:
        return (False, "New password must be at least 6 characters long.")
    salt, pwd_hash = hash_password(new_password)
    users[key] = replace(
        users[key],
        password_salt=salt,
        password_hash=pwd_hash,
    )
    return (True, "Password has been successfully reset! You can now sign in.")


def send_resend_recovery_email(
    *,
    api_key: str,
    to_email: str,
    full_name: str,
    username: str,
    code: str,
    from_email: str = "Academic Portal <onboarding@resend.dev>",
) -> tuple[bool, str]:
    """Send a 6-digit password recovery code email via the Resend REST API."""
    clean_key = api_key.strip()
    clean_to = to_email.strip()
    if not clean_key:
        return (False, "Resend API key is required to send recovery emails.")
    if not clean_to or "@" not in clean_to:
        return (False, "A valid recipient email address is required.")

    email_html = (
        f"<div style='font-family:Inter,Arial,sans-serif;max-width:520px;margin:0 auto;"
        f"padding:28px;border:1px solid #e2e8f0;border-radius:14px;background:#ffffff;'>"
        f"<h2 style='color:#1e3a8a;margin:0 0 8px 0;'>🎓 Password Recovery Code</h2>"
        f"<p style='color:#334155;font-size:14px;line-height:1.6;'>"
        f"Hello <strong>{html.escape(full_name)}</strong> (username: <code>{html.escape(username)}</code>),<br>"
        f"Use the 6-digit verification code below to reset your Student Grade &amp; Report Card Portal password:"
        f"</p>"
        f"<div style='background:#eff6ff;border:2px dashed #3b82f6;border-radius:12px;"
        f"padding:18px;text-align:center;margin:20px 0;'>"
        f"<span style='font-size:30px;font-weight:800;letter-spacing:6px;color:#1e3a8a;'>"
        f"{html.escape(code)}"
        f"</span>"
        f"</div>"
        f"<p style='color:#64748b;font-size:12px;margin:0;'>"
        f"If you did not request a password reset, you can safely ignore this email."
        f"</p>"
        f"</div>"
    )

    payload = json.dumps(
        {
            "from": from_email,
            "to": [clean_to],
            "subject": f"Your Password Recovery Code: {code}",
            "html": email_html,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {clean_key}",
            "Content-Type": "application/json",
            "User-Agent": "StudentReportCardPortal/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            if 200 <= resp.status < 300:
                return (True, f"Recovery code sent to {clean_to} via Resend!")
            return (False, f"Resend returned status {resp.status}.")
    except urllib.error.HTTPError as exc:
        try:
            err_body = exc.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            err_body = str(exc)
        return (False, f"Resend API error ({exc.code}): {err_body}")
    except Exception as exc:  # noqa: BLE001
        return (False, f"Could not reach Resend API: {exc}")
