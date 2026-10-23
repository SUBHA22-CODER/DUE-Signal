import aiosqlite
import os
from datetime import datetime, timezone, timedelta

DB_PATH = os.getenv("DUE_SIGNAL_DB", "duesignal.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS deadlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    course TEXT NOT NULL,
    due_at TEXT NOT NULL,
    weight_pct REAL DEFAULT 0,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(title, due_at)
);
CREATE INDEX IF NOT EXISTS idx_deadlines_status_due ON deadlines(status, due_at);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()

async def list_deadlines(window_days: int = 7):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT id, title, course, due_at, weight_pct, status
               FROM deadlines
               WHERE status = 'pending'
                 AND datetime(due_at) <= datetime('now', ?)
               ORDER BY datetime(due_at) ASC""",
            (f"+{int(window_days)} days",),
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {"id": r[0], "title": r[1], "course": r[2],
                 "due_at": r[3], "weight_pct": r[4], "status": r[5]}
                for r in rows
            ]

async def add_deadline(title: str, course: str, due_at: str, weight_pct: float = 0):
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            async with db.execute(
                """INSERT INTO deadlines (title, course, due_at, weight_pct)
                   VALUES (?, ?, ?, ?)""",
                (title, course, due_at, weight_pct),
            ) as cursor:
                await db.commit()
                return {"id": cursor.lastrowid, "created": True}
        except aiosqlite.IntegrityError:
            async with db.execute(
                "SELECT id FROM deadlines WHERE title = ? AND due_at = ?",
                (title, due_at),
            ) as cursor:
                row = await cursor.fetchone()
                return {"id": row[0] if row else None, "created": False}

async def mark_complete(deadline_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "UPDATE deadlines SET status = 'completed' WHERE id = ?", (deadline_id,)
        ) as cursor:
            await db.commit()
            if cursor.rowcount == 0:
                raise ValueError(f"Deadline {deadline_id} not found")
            return {"id": deadline_id, "status": "completed"}

async def clear_all_deadlines():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM deadlines")
        await db.commit()
        return {"cleared": True}

async def count_deadlines():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*), SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) FROM deadlines") as cursor:
            row = await cursor.fetchone()
            return {"total": row[0] or 0, "pending": row[1] or 0}

async def seed_scenario(scenario_name: str = "finals_crisis"):
    await init_db()
    await clear_all_deadlines()
    now = datetime.now(timezone.utc)
    
    if scenario_name == "finals_crisis":
        items = [
            ("Operating Systems Kernel Lab", "CS301", (now - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M"), 20.0),
            ("Distributed Systems Midterm", "CS350", (now + timedelta(hours=14)).strftime("%Y-%m-%dT%H:%M"), 35.0),
            ("Algorithm Problem Set 6", "CS261", (now + timedelta(hours=42)).strftime("%Y-%m-%dT%H:%M"), 15.0),
            ("Ethics in AI Discussion Post", "PHIL110", (now + timedelta(hours=80)).strftime("%Y-%m-%dT%H:%M"), 5.0),
            ("Senior Honors Thesis Draft", "HON499", (now + timedelta(days=12)).strftime("%Y-%m-%dT%H:%M"), 40.0),
        ]
    else: # midterms
        items = [
            ("Linear Algebra Quiz 4", "MATH201", (now + timedelta(hours=18)).strftime("%Y-%m-%dT%H:%M"), 10.0),
            ("Machine Learning Assignment 2", "CS229", (now + timedelta(hours=36)).strftime("%Y-%m-%dT%H:%M"), 25.0),
            ("Database Systems Normalization HW", "CS145", (now + timedelta(hours=96)).strftime("%Y-%m-%dT%H:%M"), 15.0),
        ]
        
    created_ids = []
    for title, course, due_at, weight in items:
        res = await add_deadline(title, course, due_at, weight)
        created_ids.append(res["id"])
    return {"scenario": scenario_name, "count": len(created_ids), "ids": created_ids}
