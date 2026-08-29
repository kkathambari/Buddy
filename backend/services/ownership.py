"""Server-side companion ownership checks.

Ownership is deliberately stored separately from mutable companion state so a
client cannot transfer ownership by writing a crafted sync payload.
"""

from backend.repositories.sqlite import get_connection
from core.logging import setup_logger

logger = setup_logger("ownership")


def init_ownership_store() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS companion_owners (
                companion_id TEXT PRIMARY KEY,
                user_uid TEXT NOT NULL,
                created_at REAL NOT NULL DEFAULT (unixepoch())
            )"""
        )
        conn.commit()
    finally:
        conn.close()


def claim_companion(user_uid: str, companion_id: str) -> bool:
    """Claim an unowned companion, or allow its existing owner to relink it."""
    init_ownership_store()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT user_uid FROM companion_owners WHERE companion_id = ?", (companion_id,)
        ).fetchone()
        if row and row["user_uid"] != user_uid:
            return False
        if not row:
            conn.execute(
                "INSERT INTO companion_owners (companion_id, user_uid) VALUES (?, ?)",
                (companion_id, user_uid),
            )
            conn.commit()
        return True
    finally:
        conn.close()


def user_owns_companion(user_uid: str, companion_id: str) -> bool:
    init_ownership_store()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM companion_owners WHERE companion_id = ? AND user_uid = ?",
            (companion_id, user_uid),
        ).fetchone()
        return row is not None
    finally:
        conn.close()
