import psycopg2
import json
from config import PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=PGHOST,
            port=PGPORT,
            database=PGDATABASE,
            user=PGUSER,
            password=PGPASSWORD
        )
        self.create_table()

    def create_table(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS release_plan_cache (
                    id SERIAL PRIMARY KEY,
                    data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        self.conn.commit()

    def cache_data(self, data):
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM release_plan_cache")
            cur.execute("INSERT INTO release_plan_cache (data) VALUES (%s)", (json.dumps(data),))
        self.conn.commit()

    def get_cached_data(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT data FROM release_plan_cache ORDER BY created_at DESC LIMIT 1")
            result = cur.fetchone()
        return result[0] if result else None

    def __del__(self):
        self.conn.close()
