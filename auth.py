"""Authentication, role-based access control, and user management."""

from __future__ import annotations

import hashlib
import hmac
import random
import secrets
from dataclasses import dataclass

ROLE_STUDENT = "Student"
ROLE_TEACHER = "Teacher"
ROLE_ADMIN = "Administrator"
VALID_ROLES = (ROLE_STUDENT, ROLE_TEACHER, ROLE_ADMIN)
DEMO_STUDENT_USERNAMES = ("alex", "sam", "priya")

RANDOM_ASSIGNMENT_POOL: tuple[tuple[str, float, float], ...] = (
    ("Mathematics — Unit Test #1", 100.0, 1.0),
    ("Chemistry — Titration Lab Report", 100.0, 1.0),
    ("English Literature — Critical Essay", 100.0, 1.0),
    ("World History — Source Analysis Quiz", 100.0, 1.0),
    ("Computer Science — Algorithm Project", 100.0, 1.0),
    ("Physics — Mechanics Midterm Exam", 100.0, 1.0),
    ("Biology — Cellular Respiration Lab", 100.0, 1.0),
    ("Economics — Macroeconomics Quiz", 100.0, 1.0),
    ("Calculus — Derivatives Assessment", 100.0, 1.0),
    ("Art & Design — Portfolio Critique", 100.0, 1.0),
)


def generate_random_demo_assignments(count: int = 5) -> list[dict[str, object]]:
    """Generate randomized assignment & test results for demo student logins only."""
    chosen = random.sample(RANDOM_ASSIGNMENT_POOL, k=min(count, len(RANDOM_ASSIGNMENT_POOL)))
    rows: list[dict[str, object]] = []
    for idx, (title, max_marks, credits) in enumerate(chosen, start=1):
        score = float(random.randint(58, 99))
        rows.append(
            {
                "id": idx,
                "name": title,
                "marks": score,
                "max_marks": max_marks,
                "credits": credits,
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
    )


def get_default_users() -> dict[str, UserAccount]:
    """Return pre-seeded demo accounts for Student, Teacher, and Administrator."""
    accounts = [
        _make_user(
            username="alex",
            password="student123",
            full_name="Alex Johnson",
            role=ROLE_STUDENT,
            student_id="STU-2026-104",
            grade_level="Grade 11",
            fixed_salt="a1b2c3d4e5f60718293a4b5c6d7e8f90",
        ),
        _make_user(
            username="sam",
            password="student123",
            full_name="Sam Rivera",
            role=ROLE_STUDENT,
            student_id="STU-2026-209",
            grade_level="Grade 12",
            fixed_salt="f0e9d8c7b6a594837261504f3e2d1c0b",
        ),
        _make_user(
            username="priya",
            password="student123",
            full_name="Priya Patel",
            role=ROLE_STUDENT,
            student_id="STU-2026-315",
            grade_level="Grade 11",
            fixed_salt="99887766554433221100ffeeddccbbaa",
        ),
        _make_user(
            username="teacher",
            password="teacher123",
            full_name="Prof. Sarah Jenkins",
            role=ROLE_TEACHER,
            student_id="TCH-2026-01",
            grade_level="Senior Faculty",
            fixed_salt="11223344556677889900aabbccddeeff",
        ),
        _make_user(
            username="admin",
            password="admin123",
            full_name="Dr. Marcus Sterling",
            role=ROLE_ADMIN,
            student_id="ADM-2026-01",
            grade_level="Principal & Registrar",
            fixed_salt="abcdef0123456789abcdef0123456789",
        ),
    ]
    return {acct.username: acct for acct in accounts}


def get_default_student_roster() -> dict[str, dict[str, object]]:
    """Return initial multi-student academic records for Demo views."""
    return {
        "STU-2026-104": {
            "student_name": "Alex Johnson",
            "student_id": "STU-2026-104",
            "grade_level": "Grade 11",
            "school_name": DEFAULT_SCHOOL,
            "username": "alex",
            "is_demo": True,
            "custom_remarks": "",
            "subjects": generate_random_demo_assignments(5),
        },
        "STU-2026-209": {
            "student_name": "Sam Rivera",
            "student_id": "STU-2026-209",
            "grade_level": "Grade 12",
            "school_name": DEFAULT_SCHOOL,
            "username": "sam",
            "is_demo": True,
            "custom_remarks": "",
            "subjects": generate_random_demo_assignments(5),
        },
        "STU-2026-315": {
            "student_name": "Priya Patel",
            "student_id": "STU-2026-315",
            "grade_level": "Grade 11",
            "school_name": DEFAULT_SCHOOL,
            "username": "priya",
            "is_demo": True,
            "custom_remarks": "Scheduled for weekly Mathematics tutoring session.",
            "subjects": generate_random_demo_assignments(5),
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
    student_id: str = "STU-2026-500",
    grade_level: str = "Grade 11",
    school_name: str = DEFAULT_SCHOOL,
) -> tuple[UserAccount | None, str | None]:
    """Register a new Student, Teacher, or Administrator account.

    Returns (UserAccount, None) on success or (None, error_message) on failure.
    """
    clean_user = username.strip().lower()
    clean_name = full_name.strip()
    clean_id = student_id.strip() or "STU-2026-500"
    clean_grade = grade_level.strip() or "Grade 11"
    clean_school = school_name.strip() or DEFAULT_SCHOOL

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
