import aiosqlite
import os

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
