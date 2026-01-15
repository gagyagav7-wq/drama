import sqlite3

DB_NAME = "history_drama.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS uploads 
                 (platform TEXT, drama_id TEXT, ep_name TEXT, UNIQUE(platform, drama_id, ep_name))''')
    conn.commit()
    conn.close()

def is_duplicate(platform, drama_id, ep_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT 1 FROM uploads WHERE platform=? AND drama_id=? AND ep_name=?", (platform, drama_id, ep_name))
    res = c.fetchone()
    conn.close()
    return res is not None

def save_history(platform, drama_id, ep_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO uploads VALUES (?, ?, ?)", (platform, drama_id, ep_name))
        conn.commit()
    except: pass
    conn.close()
  
