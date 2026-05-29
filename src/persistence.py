import sqlite3
import threading


class Persistence:
    def __init__(self, db_path):
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.commit()

    def execute(self, sql, params=None) -> list[tuple]:
        with self._lock:
            cursor = self._conn.execute(sql, params or ())
            rows = cursor.fetchall()
            self._conn.commit()
            return rows

    def define(self, schema_sql):
        with self._lock:
            self._conn.execute(schema_sql)
            self._conn.commit()
