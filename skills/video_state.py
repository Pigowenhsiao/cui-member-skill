"""Small SQLite stage ledger for resumable per-video processing."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

try:
    from .path_utils import project_path
except ImportError:
    from path_utils import project_path

DB_PATH = project_path("logs/video_state.sqlite3")
STAGES = ("pending", "audio", "transcript_ready", "complete")


def _connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = project_path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("""CREATE TABLE IF NOT EXISTS video_state (
        video_id TEXT PRIMARY KEY,
        title TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'pending',
        subtitle_error TEXT NOT NULL DEFAULT '',
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    return connection


def get(video_id: str, db_path: str | Path | None = None) -> dict | None:
    with closing(_connect(db_path)) as db:
        row = db.execute("SELECT video_id,title,status,subtitle_error FROM video_state WHERE video_id=?", (video_id,)).fetchone()
    return None if row is None else dict(zip(("video_id", "title", "status", "subtitle_error"), row))


def is_complete(video_id: str, db_path: str | Path | None = None) -> bool:
    state = get(video_id, db_path)
    return bool(state and state["status"] == "complete")


def mark(video_id: str, stage: str, *, title: str = "", subtitle_error: str | None = None,
         db_path: str | Path | None = None) -> None:
    if stage not in STAGES:
        raise ValueError(f"Unknown processing stage: {stage}")
    with closing(_connect(db_path)) as db:
        with db:
            db.execute("""INSERT INTO video_state(video_id,title,status,subtitle_error,updated_at)
                VALUES(?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(video_id) DO UPDATE SET
                title=CASE WHEN excluded.title='' THEN video_state.title ELSE excluded.title END,
                status=excluded.status,
                subtitle_error=CASE WHEN ? IS NULL THEN video_state.subtitle_error ELSE ? END,
                updated_at=CURRENT_TIMESTAMP""",
                (video_id, title, stage, subtitle_error or "", subtitle_error, subtitle_error))


