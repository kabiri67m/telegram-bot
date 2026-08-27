import time
from database import get_conn
from config import FLOOD_MAX_MESSAGES, FLOOD_INTERVAL_SECONDS


def check_flood(chat_id, user_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT last_ts, count FROM flood WHERE chat_id=? AND user_id=?",
        (chat_id, user_id),
    )
    row = cur.fetchone()

    now = int(time.time())

    if row:
        last_ts, count = row

        if now - last_ts <= FLOOD_INTERVAL_SECONDS:
            count += 1
        else:
            count = 1

        cur.execute(
            "INSERT OR REPLACE INTO flood (chat_id, user_id, last_ts, count) VALUES (?, ?, ?, ?)",
            (chat_id, user_id, now, count),
        )
        conn.commit()
        conn.close()

        return count >= FLOOD_MAX_MESSAGES

    else:
        cur.execute(
            "INSERT INTO flood (chat_id, user_id, last_ts, count) VALUES (?, ?, ?, ?)",
            (chat_id, user_id, now, 1),
        )
        conn.commit()
        conn.close()
        return False
