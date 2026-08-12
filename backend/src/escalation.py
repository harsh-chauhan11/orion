import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import uuid


DATABASE_PATH = Path(__file__).resolve().parent.parent / "orion_memory.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS escalations (
            request_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            issue TEXT NOT NULL,
            agent_checked TEXT NOT NULL,
            urgency TEXT NOT NULL,
            language TEXT NOT NULL,
            preferred_follow_up TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()

    return connection


def create_escalation(
    user_id: str,
    name: str,
    issue: str,
    agent_checked: str,
    urgency: str,
    language: str,
    preferred_follow_up: str,
) -> dict:

    connection = get_connection()

    try:
        timestamp = datetime.now(timezone.utc)

        request_id = (
            f"ESC-{timestamp.strftime('%Y%m%d')}-"
            f"{uuid.uuid4().hex[:6].upper()}"
        )

        created_at = timestamp.isoformat()

        connection.execute(
            """
            INSERT INTO escalations (
                request_id,
                user_id,
                name,
                issue,
                agent_checked,
                urgency,
                language,
                preferred_follow_up,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                user_id,
                name,
                issue,
                agent_checked,
                urgency,
                language,
                preferred_follow_up,
                "open",
                created_at,
            ),
        )

        connection.commit()

        return {
            "success": True,
            "request_id": request_id,
            "status": "open",
            "created_at": created_at,
        }

    finally:
        connection.close()


def get_escalations() -> list[dict]:

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                request_id,
                user_id,
                name,
                issue,
                agent_checked,
                urgency,
                language,
                preferred_follow_up,
                status,
                created_at
            FROM escalations
            ORDER BY created_at DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()