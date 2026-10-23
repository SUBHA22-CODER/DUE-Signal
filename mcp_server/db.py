import aiosqlite
import os
from datetime import datetime, timezone, timedelta

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

def get_db():
    db_path = os.getenv("DUE_SIGNAL_DB", "duesignal.db")
    return aiosqlite.connect(db_path, timeout=15.0)

async def init_db():
    async with get_db() as db:
        await db.executescript(SCHEMA)
        await db.commit()

async def list_deadlines(window_days: int = 7):
    async with get_db() as db:
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

async def list_deadlines_filtered(status: str = "pending", window_days: int = 90, course: str = None, search: str = None):
    query = "SELECT id, title, course, due_at, weight_pct, status FROM deadlines WHERE 1=1"
    params = []

    if status and status != "all":
        query += " AND status = ?"
        params.append(status)

    if window_days:
        query += " AND datetime(due_at) <= datetime('now', ?)"
        params.append(f"+{int(window_days)} days")

    if course:
        query += " AND course LIKE ?"
        params.append(f"%{course}%")

    if search:
        query += " AND (title LIKE ? OR course LIKE ?)"
        params.append(f"%{search}%")
        params.append(f"%{search}%")

    query += " ORDER BY datetime(due_at) ASC"

    async with get_db() as db:
        async with db.execute(query, tuple(params)) as cursor:
            rows = await cursor.fetchall()
            return [
                {"id": r[0], "title": r[1], "course": r[2],
                 "due_at": r[3], "weight_pct": r[4], "status": r[5]}
                for r in rows
            ]

async def get_deadline(deadline_id: int):
    async with get_db() as db:
        async with db.execute(
            "SELECT id, title, course, due_at, weight_pct, status FROM deadlines WHERE id = ?",
            (deadline_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return {
                "id": row[0], "title": row[1], "course": row[2],
                "due_at": row[3], "weight_pct": row[4], "status": row[5]
            }

async def add_deadline(title: str, course: str, due_at: str, weight_pct: float = 0):
    async with get_db() as db:
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

async def update_deadline(deadline_id: int, title: str, course: str, due_at: str, weight_pct: float):
    async with get_db() as db:
        async with db.execute(
            """UPDATE deadlines 
               SET title = ?, course = ?, due_at = ?, weight_pct = ?
               WHERE id = ?""",
            (title, course, due_at, weight_pct, deadline_id)
        ) as cursor:
            await db.commit()
            if cursor.rowcount == 0:
                raise ValueError(f"Deadline {deadline_id} not found")
            return {"id": deadline_id, "updated": True}

async def mark_complete(deadline_id: int):
    async with get_db() as db:
        async with db.execute(
            "UPDATE deadlines SET status = 'completed' WHERE id = ?", (deadline_id,)
        ) as cursor:
            await db.commit()
            if cursor.rowcount == 0:
                raise ValueError(f"Deadline {deadline_id} not found")
            return {"id": deadline_id, "status": "completed"}

async def reopen_deadline(deadline_id: int):
    async with get_db() as db:
        async with db.execute(
            "UPDATE deadlines SET status = 'pending' WHERE id = ?", (deadline_id,)
        ) as cursor:
            await db.commit()
            if cursor.rowcount == 0:
                raise ValueError(f"Deadline {deadline_id} not found")
            return {"id": deadline_id, "status": "pending"}

async def delete_deadline(deadline_id: int):
    async with get_db() as db:
        async with db.execute(
            "DELETE FROM deadlines WHERE id = ?", (deadline_id,)
        ) as cursor:
            await db.commit()
            if cursor.rowcount == 0:
                raise ValueError(f"Deadline {deadline_id} not found")
            return {"id": deadline_id, "deleted": True}

async def clear_all_deadlines():
    async with get_db() as db:
        await db.execute("DELETE FROM deadlines")
        await db.commit()
        return {"cleared": True}

async def count_deadlines():
    async with get_db() as db:
        async with db.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed
            FROM deadlines
        """) as cursor:
            row = await cursor.fetchone()
            total = row[0] or 0
            pending = row[1] or 0
            completed = row[2] or 0
            rate = round((completed / total * 100), 1) if total > 0 else 0.0
            return {
                "total": total,
                "pending": pending,
                "completed": completed,
                "completion_rate_pct": rate
            }

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
