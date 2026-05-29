import threading

from src.persistence import Persistence


class TestExecute:
    def test_insert_returns_empty_list(self, tmp_path):
        db = Persistence(tmp_path / "notes.db")
        db.define("CREATE TABLE items (value TEXT)")

        result = db.execute("INSERT INTO items VALUES ('hello')")

        assert result == []

    def test_select_returns_rows_as_list_of_tuples(self, tmp_path):
        db = Persistence(tmp_path / "notes.db")
        db.define("CREATE TABLE items (value TEXT)")
        db.execute("INSERT INTO items VALUES ('hello')")
        db.execute("INSERT INTO items VALUES ('world')")

        result = db.execute("SELECT value FROM items ORDER BY value")

        assert result == [("hello",), ("world",)]

    def test_returning_clause_yields_inserted_row(self, tmp_path):
        db = Persistence(tmp_path / "notes.db")
        db.define("CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, value TEXT)")

        result = db.execute("INSERT INTO items (value) VALUES ('ping') RETURNING id, value")

        assert result == [(1, "ping")]

    def test_parameterized_query_binds_values_safely(self, tmp_path):
        db = Persistence(tmp_path / "notes.db")
        db.define("CREATE TABLE items (name TEXT, score INTEGER)")
        db.execute("INSERT INTO items VALUES (?, ?)", ("alice", 42))

        result = db.execute("SELECT name, score FROM items WHERE name = ?", ("alice",))

        assert result == [("alice", 42)]


class TestDefine:
    def test_table_is_writable_and_readable_after_define(self, tmp_path):
        db = Persistence(tmp_path / "notes.db")

        db.define("CREATE TABLE notes (body TEXT)")
        db.execute("INSERT INTO notes VALUES ('first note')")
        result = db.execute("SELECT body FROM notes")

        assert result == [("first note",)]


class TestThreadSafety:
    def test_concurrent_inserts_preserve_all_rows(self, tmp_path):
        db = Persistence(tmp_path / "notes.db")
        db.define("CREATE TABLE events (val INTEGER)")
        thread_count = 10

        threads = [
            threading.Thread(target=db.execute, args=("INSERT INTO events VALUES (?)", (i,)))
            for i in range(thread_count)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        rows = db.execute("SELECT COUNT(*) FROM events")
        assert rows == [(thread_count,)]
