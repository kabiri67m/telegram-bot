from database import get_conn


def set_role(chat_id, user_id, role):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO roles (chat_id, user_id, role) VALUES (?, ?, ?)",
        (chat_id, user_id, role),
    )
    conn.commit()
    conn.close()


def get_role(chat_id, user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT role FROM roles WHERE chat_id=? AND user_id=?",
        (chat_id, user_id),
    )
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def remove_role(chat_id, user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM roles WHERE chat_id=? AND user_id=?",
        (chat_id, user_id),
    )
    conn.commit()
    conn.close()
