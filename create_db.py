import sqlite3
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_name="search_data.db"):
        self.db_name = db_name

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        try:
            yield conn
        finally:
            conn.close()

    def create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            tables = {
                "sorular": """
                    CREATE TABLE IF NOT EXISTS sorular (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        soru TEXT NOT NULL UNIQUE,
                        bilgi_mesaji TEXT DEFAULT NULL
                    )
                """,
                "etiketler": """
                    CREATE TABLE IF NOT EXISTS etiketler (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        etiket TEXT UNIQUE NOT NULL
                    )
                """,
                "etiket_kelimeleri": """
                    CREATE TABLE IF NOT EXISTS etiket_kelimeleri (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        etiket_id INTEGER,
                        kelime TEXT NOT NULL,
                        FOREIGN KEY (etiket_id) REFERENCES etiketler(id) ON DELETE CASCADE
                    )
                """,
                "soru_etiketleri": """
                    CREATE TABLE IF NOT EXISTS soru_etiketleri (
                        soru_id INTEGER,
                        etiket_id INTEGER,
                        FOREIGN KEY (soru_id) REFERENCES sorular(id) ON DELETE CASCADE,
                        FOREIGN KEY (etiket_id) REFERENCES etiketler(id) ON DELETE CASCADE,
                        PRIMARY KEY (soru_id, etiket_id)
                    )
                """
            }
            for table, query in tables.items():
                cursor.execute(query)
            conn.commit()

    def get_bilgi_mesaji(self, soru):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT bilgi_mesaji FROM sorular WHERE soru = ?", (soru,))
            result = cursor.fetchone()
            return result[0] if result else "Bilgi mesajı bulunamadı."

if __name__ == "__main__":
    db_manager = DatabaseManager()
    print("✅ Veritabanı başarıyla oluşturuldu!")