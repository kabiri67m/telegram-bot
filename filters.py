from database import get_conn


def add_filter(chat_id, word):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO filters (chat_id, word) VALUES (?, ?)",
        (chat_id, word.lower()),
    )
    conn.commit()
    conn.close()


def remove_filter(chat_id, word):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM filters WHERE chat_id=? AND word=?",
        (chat_id, word.lower()),
    )
    conn.commit()
    conn.close()


def get_filters(chat_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT word FROM filters WHERE chat_id=?",
        (chat_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]
