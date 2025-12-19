import sqlite3
from config import Config

class DatabaseManager:
    def __init__(self):
        self.db_name = Config.DB_NAME
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
        except Exception as e:
            print(f"❌ DB Init Error: {e}")

    def save_message(self, chat_id, role, content):
        try:
            with sqlite3.connect(self.db_name) as conn:
                conn.execute("INSERT INTO history (chat_id, role, content) VALUES (?, ?, ?)", 
                             (str(chat_id), role, content))
        except Exception as e:
            print(f"⚠️ DB Save Error: {e}")

    def load_history(self, chat_id):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.execute(
                    "SELECT role, content FROM history WHERE chat_id = ? ORDER BY id ASC LIMIT 20", 
                    (str(chat_id),)
                )
                rows = cursor.fetchall()
            
            formatted = []
            for role, content in rows:
                formatted.append({"role": role, "parts": [content]})
            return formatted
        except Exception as e:
            print(f"⚠️ DB Load Error: {e}")
            return []
