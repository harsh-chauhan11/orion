import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent.parent / "orion_memory.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            facts TEXT NOT NULL DEFAULT '{}',
            last_interaction TEXT NOT NULL
        )
        """
    )

    connection.commit()
    return connection


def lookup_user(user_id: str) -> dict | None:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT user_id, name, facts, last_interaction
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        if row is None:
            return None

        return {
            "user_id": row["user_id"],
            "name": row["name"],
            "facts": json.loads(row["facts"]),
            "last_interaction": row["last_interaction"],
        }

    finally:
        connection.close()


def save_user_memory(
    user_id: str,
    name: str,
    facts: dict,
) -> dict:
    connection = get_connection()

    try:
        now = datetime.now(timezone.utc).isoformat()

        existing = connection.execute(
            """
            SELECT facts
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        if existing:
            existing_facts = json.loads(existing["facts"])
            existing_facts.update(facts)
            facts = existing_facts

        connection.execute(
            """
            INSERT INTO users (user_id, name, facts, last_interaction)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET
                name = excluded.name,
                facts = excluded.facts,
                last_interaction = excluded.last_interaction
            """,
            (
                user_id,
                name,
                json.dumps(facts),
                now,
            ),
        )

        connection.commit()

        return {
            "user_id": user_id,
            "name": name,
            "facts": facts,
            "last_interaction": now,
        }

    finally:
        connection.close()