# database.py
import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_name='recipes.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.init_db()
        print("✅ База данных подключена")

    def init_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER UNIQUE,
                username TEXT,
                created_at TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                recipe_id TEXT,
                recipe_name TEXT,
                recipe_data TEXT,
                saved_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        self.conn.commit()

    def add_user(self, tg_id, username):
        self.cursor.execute(
            "INSERT OR IGNORE INTO users (tg_id, username, created_at) VALUES (?, ?, ?)",
            (tg_id, username, datetime.now())
        )
        self.conn.commit()

    def add_favorite(self, tg_id, recipe_id, recipe_name, recipe_data):
        self.cursor.execute("SELECT id FROM users WHERE tg_id = ?", (tg_id,))
        user = self.cursor.fetchone()
        if user:
            self.cursor.execute(
                "INSERT INTO favorites (user_id, recipe_id, recipe_name, recipe_data, saved_at) VALUES (?, ?, ?, ?, ?)",
                (user[0], recipe_id, recipe_name, json.dumps(recipe_data), datetime.now())
            )
            self.conn.commit()
            return True
        return False

    def get_favorites(self, tg_id):
        self.cursor.execute("""
            SELECT f.recipe_id, f.recipe_name, f.recipe_data 
            FROM favorites f
            JOIN users u ON u.id = f.user_id
            WHERE u.tg_id = ?
            ORDER BY f.saved_at DESC
        """, (tg_id,))
        return self.cursor.fetchall()
    
    # 🔥 НОВАЯ ФУНКЦИЯ: очистка всего избранного
    def clear_favorites(self, tg_id):
        """Удаляет все избранные рецепты пользователя"""
        self.cursor.execute("""
            DELETE FROM favorites 
            WHERE user_id = (SELECT id FROM users WHERE tg_id = ?)
        """, (tg_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0  # вернёт True, если что-то удалилось