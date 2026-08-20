from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.core.conditions import supported_conditions


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    age INTEGER,
    gender TEXT,
    height_cm REAL,
    weight_kg REAL,
    conditions_json TEXT NOT NULL DEFAULT '[]',
    allergies_json TEXT NOT NULL DEFAULT '[]',
    dietary_restrictions_json TEXT NOT NULL DEFAULT '[]',
    notes TEXT NOT NULL DEFAULT '',
    onboarding_completed INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    dose TEXT NOT NULL,
    frequency INTEGER NOT NULL DEFAULT 1,
    dose_times_json TEXT NOT NULL DEFAULT '[]',
    start_date TEXT NOT NULL,
    end_date TEXT,
    is_permanent INTEGER NOT NULL DEFAULT 1,
    food_relation TEXT,
    notes TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS dose_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_id INTEGER NOT NULL REFERENCES medications(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scheduled_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('upcoming','taken','missed','skipped')),
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(medication_id, scheduled_at)
);
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    response_json TEXT NOT NULL,
    intent TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS symptoms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    symptoms TEXT NOT NULL,
    started_at TEXT,
    severity INTEGER,
    classification TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS food_lookup_cache (
    query_key TEXT PRIMARY KEY,
    response_json TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS food_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    mode TEXT NOT NULL,
    items_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_medications_user ON medications(user_id, active);
CREATE INDEX IF NOT EXISTS idx_dose_events_user_date ON dose_events(user_id, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_food_history_user ON food_history(user_id, created_at DESC);
"""


class Database:
    def __init__(self, path: Path):
        self.path = path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, check_same_thread=False, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            profile_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(profiles)")
            }
            if "onboarding_completed" not in profile_columns:
                connection.execute(
                    "ALTER TABLE profiles ADD COLUMN onboarding_completed INTEGER NOT NULL DEFAULT 1"
                )
            food_history_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(food_history)")
            }
            if "conversation_id" not in food_history_columns:
                connection.execute(
                    "ALTER TABLE food_history ADD COLUMN conversation_id INTEGER REFERENCES conversations(id) ON DELETE SET NULL"
                )
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_food_history_conversation ON food_history(conversation_id)"
            )
            rows = connection.execute(
                "SELECT user_id,conditions_json FROM profiles"
            ).fetchall()
            for row in rows:
                try:
                    stored_conditions = json.loads(row["conditions_json"])
                except (json.JSONDecodeError, TypeError):
                    stored_conditions = []
                cleaned_conditions = supported_conditions(stored_conditions)
                if cleaned_conditions != stored_conditions:
                    connection.execute(
                        "UPDATE profiles SET conditions_json=? WHERE user_id=?",
                        (json.dumps(cleaned_conditions), row["user_id"]),
                    )
            conversation_rows = connection.execute(
                """
                SELECT id,user_id,question,response_json,intent,created_at
                FROM conversations
                WHERE user_id IS NOT NULL AND COALESCE(intent, '') != 'source_follow_up'
                """
            ).fetchall()
            for row in conversation_rows:
                try:
                    response = json.loads(row["response_json"])
                except (json.JSONDecodeError, TypeError):
                    continue
                nutrition_items = response.get("nutrition_items") or []
                if not nutrition_items:
                    continue
                connection.execute(
                    """
                    INSERT OR IGNORE INTO food_history
                        (user_id,conversation_id,question,mode,items_json,created_at)
                    VALUES (?,?,?,?,?,?)
                    """,
                    (
                        row["user_id"],
                        row["id"],
                        row["question"],
                        row["intent"] or "chat",
                        json.dumps(nutrition_items, ensure_ascii=False),
                        row["created_at"],
                    ),
                )

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
