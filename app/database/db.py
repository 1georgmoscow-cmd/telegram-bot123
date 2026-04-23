import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Any


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with closing(self._connect()) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS work_days (
                    date TEXT PRIMARY KEY,
                    is_closed INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS time_slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    UNIQUE(date, time)
                );

                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    reminder_job_id TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    def add_work_day(self, date: str) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                """
                INSERT INTO work_days(date, is_closed)
                VALUES(?, 0)
                ON CONFLICT(date) DO UPDATE SET is_closed = 0
                """,
                (date,),
            )
            conn.commit()

    def close_day(self, date: str) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                """
                INSERT INTO work_days(date, is_closed)
                VALUES(?, 1)
                ON CONFLICT(date) DO UPDATE SET is_closed = 1
                """,
                (date,),
            )
            conn.commit()

    def add_slot(self, date: str, time: str) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                """
                INSERT INTO work_days(date, is_closed)
                VALUES(?, 0)
                ON CONFLICT(date) DO NOTHING
                """,
                (date,),
            )
            conn.execute(
                """
                INSERT INTO time_slots(date, time, is_active)
                VALUES(?, ?, 1)
                ON CONFLICT(date, time) DO UPDATE SET is_active = 1
                """,
                (date, time),
            )
            conn.commit()

    def delete_slot(self, date: str, time: str) -> int:
        with closing(self._connect()) as conn:
            cursor = conn.execute(
                """
                UPDATE time_slots
                SET is_active = 0
                WHERE date = ? AND time = ?
                """,
                (date, time),
            )
            conn.commit()
            return cursor.rowcount

    def get_month_work_days(self, start_date: str, end_date: str) -> list[str]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT date
                FROM work_days
                WHERE date BETWEEN ? AND ?
                  AND is_closed = 0
                ORDER BY date ASC
                """,
                (start_date, end_date),
            ).fetchall()
        return [row["date"] for row in rows]

    def get_free_slots(self, date: str) -> list[str]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT s.time
                FROM time_slots s
                JOIN work_days d ON d.date = s.date
                WHERE s.date = ?
                  AND s.is_active = 1
                  AND d.is_closed = 0
                  AND NOT EXISTS (
                      SELECT 1 FROM bookings b
                      WHERE b.date = s.date
                        AND b.time = s.time
                        AND b.status = 'active'
                  )
                ORDER BY s.time ASC
                """,
                (date,),
            ).fetchall()
        return [row["time"] for row in rows]

    def has_active_booking(self, user_id: int) -> bool:
        with closing(self._connect()) as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM bookings
                WHERE user_id = ? AND status = 'active'
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        return row is not None

    def create_booking(
        self,
        user_id: int,
        name: str,
        phone: str,
        date: str,
        time: str,
        reminder_job_id: str | None = None,
    ) -> int | None:
        with closing(self._connect()) as conn:
            existing_user_booking = conn.execute(
                """
                SELECT 1
                FROM bookings
                WHERE user_id = ? AND status = 'active'
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            if existing_user_booking is not None:
                return None

            slot_exists = conn.execute(
                """
                SELECT 1
                FROM time_slots s
                JOIN work_days d ON d.date = s.date
                WHERE s.date = ?
                  AND s.time = ?
                  AND s.is_active = 1
                  AND d.is_closed = 0
                  AND NOT EXISTS (
                      SELECT 1 FROM bookings b
                      WHERE b.date = s.date
                        AND b.time = s.time
                        AND b.status = 'active'
                  )
                LIMIT 1
                """,
                (date, time),
            ).fetchone()

            if slot_exists is None:
                return None

            cursor = conn.execute(
                """
                INSERT INTO bookings(user_id, name, phone, date, time, status, reminder_job_id, created_at)
                VALUES(?, ?, ?, ?, ?, 'active', ?, ?)
                """,
                (user_id, name, phone, date, time, reminder_job_id, datetime.utcnow().isoformat()),
            )
            conn.commit()
            return cursor.lastrowid

    def set_reminder_job_id(self, booking_id: int, job_id: str | None) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                "UPDATE bookings SET reminder_job_id = ? WHERE id = ?",
                (job_id, booking_id),
            )
            conn.commit()

    def get_active_booking(self, user_id: int) -> sqlite3.Row | None:
        with closing(self._connect()) as conn:
            row = conn.execute(
                """
                SELECT *
                FROM bookings
                WHERE user_id = ? AND status = 'active'
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        return row

    def cancel_booking_by_user(self, user_id: int) -> sqlite3.Row | None:
        with closing(self._connect()) as conn:
            booking = conn.execute(
                """
                SELECT *
                FROM bookings
                WHERE user_id = ? AND status = 'active'
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            if booking is None:
                return None
            conn.execute(
                "UPDATE bookings SET status = 'cancelled', reminder_job_id = NULL WHERE id = ?",
                (booking["id"],),
            )
            conn.commit()
            return booking

    def cancel_booking_by_id(self, booking_id: int) -> sqlite3.Row | None:
        with closing(self._connect()) as conn:
            booking = conn.execute(
                """
                SELECT *
                FROM bookings
                WHERE id = ? AND status = 'active'
                LIMIT 1
                """,
                (booking_id,),
            ).fetchone()
            if booking is None:
                return None
            conn.execute(
                "UPDATE bookings SET status = 'cancelled', reminder_job_id = NULL WHERE id = ?",
                (booking_id,),
            )
            conn.commit()
            return booking

    def get_schedule_by_date(self, date: str) -> list[dict[str, Any]]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT s.time,
                       b.id AS booking_id,
                       b.name,
                       b.phone,
                       b.user_id,
                       b.status
                FROM time_slots s
                LEFT JOIN bookings b
                  ON b.date = s.date
                 AND b.time = s.time
                 AND b.status = 'active'
                WHERE s.date = ? AND s.is_active = 1
                ORDER BY s.time ASC
                """,
                (date,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_bookings_for_date(self, date: str) -> list[sqlite3.Row]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM bookings
                WHERE date = ? AND status = 'active'
                ORDER BY time ASC
                """,
                (date,),
            ).fetchall()
        return rows

    def get_active_bookings_for_restore(self) -> list[sqlite3.Row]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM bookings
                WHERE status = 'active'
                ORDER BY date ASC, time ASC
                """
            ).fetchall()
        return rows
