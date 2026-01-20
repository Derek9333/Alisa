import sqlite3
import threading
from datetime import datetime, timedelta

DB_PATH = 'botdata.db'
_LOCK = threading.Lock()

def _connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def _ensure_tables():
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                user_id INTEGER PRIMARY KEY,
                referrer_id INTEGER,
                joined_at TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS bonuses (
                user_id INTEGER PRIMARY KEY,
                bonus_count INTEGER DEFAULT 0
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS daily_counters (
                user_id INTEGER,
                day TEXT,
                count INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, day)
            )
        ''')
        conn.commit()
        conn.close()

_ensure_tables()

def add_referral(user_id, referrer_id):
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute('INSERT OR IGNORE INTO referrals (user_id, referrer_id, joined_at) VALUES (?, ?, ?)', (user_id, referrer_id, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()

def get_referrer_id(user_id):
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute('SELECT referrer_id FROM referrals WHERE user_id = ?', (user_id,))
        row = cur.fetchone()
        conn.close()
        return row['referrer_id'] if row else None

def get_referral_count(user_id):
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) as c FROM referrals WHERE referrer_id = ?', (user_id,))
        row = cur.fetchone()
        conn.close()
        return row['c'] if row else 0

def set_bonus_count(user_id, count):
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute('INSERT OR REPLACE INTO bonuses (user_id, bonus_count) VALUES (?, ?)', (user_id, count))
        conn.commit()
        conn.close()

def get_bonus_count(user_id):
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute('SELECT bonus_count FROM bonuses WHERE user_id = ?', (user_id,))
        row = cur.fetchone()
        conn.close()
        return row['bonus_count'] if row else 0

def increment_daily_counter(user_id, day):
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute('SELECT count FROM daily_counters WHERE user_id = ? AND day = ?', (user_id, day))
        row = cur.fetchone()
        if row:
            cur.execute('UPDATE daily_counters SET count = count + 1 WHERE user_id = ? AND day = ?', (user_id, day))
        else:
            cur.execute('INSERT INTO daily_counters (user_id, day, count) VALUES (?, ?, 1)', (user_id, day))
        conn.commit()
        conn.close()

def get_daily_counter(user_id, day):
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute('SELECT count FROM daily_counters WHERE user_id = ? AND day = ?', (user_id, day))
        row = cur.fetchone()
        conn.close()
        return row['count'] if row else 0

def cleanup_old_counters(days=7):
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d')
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute('DELETE FROM daily_counters WHERE day < ?', (cutoff,))
        conn.commit()
        conn.close()
