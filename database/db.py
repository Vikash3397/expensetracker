import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash

DATABASE = Path(__file__).resolve().parent.parent / "expense_tracker.db"

SEED_EXPENSES = [
    ("Food", 450.00, "2026-05-03", "Lunch at cafe"),
    ("Transport", 120.00, "2026-05-05", "Metro recharge"),
    ("Bills", 2499.00, "2026-05-01", "Electricity bill"),
    ("Health", 650.00, "2026-05-08", "Pharmacy"),
    ("Entertainment", 399.00, "2026-05-12", "Movie tickets"),
    ("Shopping", 1899.00, "2026-05-15", "Groceries"),
    ("Other", 200.00, "2026-05-10", "Miscellaneous"),
    ("Food", 85.00, "2026-05-18", "Tea/snacks"),
]


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    db = get_db()
    try:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )
        db.commit()
    finally:
        db.close()


def seed_db():
    db = get_db()
    try:
        count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count > 0:
            return

        cursor = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        user_id = cursor.lastrowid

        for category, amount, date, description in SEED_EXPENSES:
            db.execute(
                """
                INSERT INTO expenses (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, amount, category, date, description),
            )

        db.commit()
    finally:
        db.close()


def get_user_by_email(email):
    db = get_db()
    try:
        return db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    finally:
        db.close()


def create_user(name, email, password_hash):
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        db.commit()
        return cursor.lastrowid
    finally:
        db.close()
