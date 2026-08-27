import sqlite3
from pathlib import Path

DB_PATH = Path("smart_manager.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_database():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS warnings (
        chat_id INTEGER,
        user_id INTEGER,
        count INTEGER,
        PRIMARY KEY (chat_id, user_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        chat_id INTEGER,
        user_id INTEGER,
        role TEXT,
        PRIMARY KEY (chat_id, user_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS filters (
        chat_id INTEGER,
        word TEXT,
        PRIMARY KEY (chat_id, word)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS flood (
        chat_id INTEGER,
        user_id INTEGER,
        last_ts INTEGER,
        count INTEGER,
        PRIMARY KEY (chat_id, user_id)
    )
    """)

    conn.commit()
    conn.close()


def get_warning(chat_id, user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT count FROM warnings WHERE chat_id=? AND user_id=?",
        (chat_id, user_id),
    )
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0


def add_warning(chat_id, user_id):
    count = get_warning(chat_id, user_id) + 1
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO warnings (chat_id, user_id, count) VALUES (?, ?, ?)",
        (chat_id, user_id, count),
    )
    conn.commit()
    conn.close()
    return count


def remove_warning(chat_id, user_id):
    count = max(get_warning(chat_id, user_id) - 1, 0)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO warnings (chat_id, user_id, count) VALUES (?, ?, ?)",
        (chat_id, user_id, count),
    )
    conn.commit()
    conn.close()
    return count


def reset_warnings(chat_id, user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM warnings WHERE chat_id=? AND user_id=?",
        (chat_id, user_id),
    )
    conn.commit()
    conn.close()
