from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "users.db"
DEFAULT_ITERATIONS = 200_000


class UserAlreadyExistsError(RuntimeError):
    """Raised when trying to create a user that already exists."""


class InvalidCredentialsError(RuntimeError):
    """Raised when the supplied credentials do not match any user."""


class UserNotApprovedError(RuntimeError):
    """Raised when the user exists but is still pending approval."""


@contextmanager
def get_connection() -> Iterable[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def ensure_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                iterations INTEGER NOT NULL,
                full_name TEXT,
                role TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )

        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        alter_statements = {
            "full_name": "ALTER TABLE users ADD COLUMN full_name TEXT",
            "role": "ALTER TABLE users ADD COLUMN role TEXT",
            "status": "ALTER TABLE users ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'",
            "is_admin": "ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0",
        }
        for column, ddl in alter_statements.items():
            if column not in columns:
                conn.execute(ddl)
                if column == "status":
                    conn.execute("UPDATE users SET status='approved' WHERE is_admin=1 OR status IS NULL")


def hash_password(password: str, *, salt: Optional[bytes] = None, iterations: int = DEFAULT_ITERATIONS) -> Tuple[str, str, int]:
    if salt is None:
        salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return digest.hex(), salt.hex(), iterations


def verify_password(password: str, *, password_hash: str, salt: str, iterations: int) -> bool:
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), iterations)
    return secrets.compare_digest(candidate.hex(), password_hash)


def _dict_from_row(row: sqlite3.Row | None) -> Dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    data["is_admin"] = bool(data.get("is_admin"))
    return data


def get_user_by_email(email: str) -> Dict[str, Any] | None:
    ensure_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    return _dict_from_row(row)


def create_or_update_user(
    *,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    is_admin: bool = False,
    iterations: int = DEFAULT_ITERATIONS,
) -> Dict[str, Any]:
    ensure_db()
    password_hash, salt, iterations = hash_password(password, iterations=iterations)
    normalized_email = email.strip().lower()
    desired_status = status or ("approved" if is_admin else "pending")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (email, password_hash, salt, iterations, full_name, role, status, is_admin)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                password_hash = excluded.password_hash,
                salt = excluded.salt,
                iterations = excluded.iterations,
                full_name = COALESCE(excluded.full_name, users.full_name),
                role = COALESCE(excluded.role, users.role),
                status = excluded.status,
                is_admin = excluded.is_admin
            """,
            (
                normalized_email,
                password_hash,
                salt,
                iterations,
                full_name.strip() if full_name else None,
                role.strip() if role else None,
                desired_status,
                1 if is_admin else 0,
            ),
        )
        row = conn.execute("SELECT * FROM users WHERE email = ?", (normalized_email,)).fetchone()
    return _dict_from_row(row) or {}


def register_user(*, email: str, password: str, full_name: str, role: Optional[str]) -> Dict[str, Any]:
    existing = get_user_by_email(email)
    if existing:
        raise UserAlreadyExistsError("Ya existe una cuenta con ese correo electrónico.")
    return create_or_update_user(
        email=email,
        password=password,
        full_name=full_name,
        role=role,
        status="pending",
        is_admin=False,
    )


def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    user = get_user_by_email(email)
    if not user:
        raise InvalidCredentialsError("Correo o contraseña no válidos.")
    if not verify_password(password, password_hash=user["password_hash"], salt=user["salt"], iterations=user["iterations"]):
        raise InvalidCredentialsError("Correo o contraseña no válidos.")
    if not user["is_admin"] and user.get("status") != "approved":
        raise UserNotApprovedError("Tu cuenta aún está pendiente de aprobación.")
    return user


def ensure_default_admin() -> Dict[str, Any]:
    email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@mecanica.local")
    password = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin!234")
    full_name = os.getenv("DEFAULT_ADMIN_NAME", "Administrador inicial")
    user = get_user_by_email(email)
    if user and user.get("is_admin"):
        return user
    return create_or_update_user(
        email=email,
        password=password,
        full_name=full_name,
        role="admin",
        status="approved",
        is_admin=True,
    )


def list_pending_users() -> list[Dict[str, Any]]:
    ensure_db()
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM users WHERE status = 'pending' ORDER BY created_at DESC").fetchall()
    return [_dict_from_row(row) for row in rows if row is not None]


def update_user_status(email: str, status: str) -> None:
    ensure_db()
    normalized_email = email.strip().lower()
    with get_connection() as conn:
        conn.execute("UPDATE users SET status = ? WHERE email = ?", (status, normalized_email))
