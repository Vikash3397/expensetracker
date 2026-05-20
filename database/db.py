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


def get_user_by_id(user_id):
    db = get_db()
    try:
        return db.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        db.close()


def update_user(user_id, name, email):
    db = get_db()
    try:
        db.execute(
            "UPDATE users SET name = ?, email = ? WHERE id = ?",
            (name, email, user_id),
        )
        db.commit()
    finally:
        db.close()


def update_user_password(user_id, password_hash):
    db = get_db()
    try:
        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, user_id),
        )
        db.commit()
    finally:
        db.close()


def _date_filter_clause(from_date, to_date):
    clauses = []
    params = []
    if from_date:
        clauses.append("date >= ?")
        params.append(from_date)
    if to_date:
        clauses.append("date <= ?")
        params.append(to_date)
    if not clauses:
        return "", []
    return " AND " + " AND ".join(clauses), params


def get_expenses_for_user(user_id, from_date=None, to_date=None):
    date_clause, date_params = _date_filter_clause(from_date, to_date)
    db = get_db()
    try:
        return db.execute(
            f"""
            SELECT id, category, amount, date, description
            FROM expenses
            WHERE user_id = ?{date_clause}
            ORDER BY date DESC, id DESC
            """,
            (user_id, *date_params),
        ).fetchall()
    finally:
        db.close()


def get_expense_total_for_user(user_id, from_date=None, to_date=None):
    date_clause, date_params = _date_filter_clause(from_date, to_date)
    db = get_db()
    try:
        return db.execute(
            f"SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?{date_clause}",
            (user_id, *date_params),
        ).fetchone()[0]
    finally:
        db.close()


def get_category_totals_for_user(user_id, from_date=None, to_date=None):
    date_clause, date_params = _date_filter_clause(from_date, to_date)
    db = get_db()
    try:
        return db.execute(
            f"""
            SELECT category, SUM(amount) AS total
            FROM expenses
            WHERE user_id = ?{date_clause}
            GROUP BY category
            ORDER BY total DESC
            """,
            (user_id, *date_params),
        ).fetchall()
    finally:
        db.close()
