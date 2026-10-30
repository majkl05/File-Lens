import os
import sqlite3
from pathlib import Path


def database_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    folder = base / "FileLens"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "index.db"


class SearchDatabase:
    def __init__(self, path=None):
        self.path = Path(path) if path else database_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self):
        with self.connect() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY,
                    path TEXT NOT NULL,
                    page INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    UNIQUE(path, page)
                )
            """)
            con.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
                USING fts5(path UNINDEXED, page UNINDEXED, text,
                           tokenize='unicode61 remove_diacritics 2')
            """)

    def replace_page(self, path, page, content):
        with self.connect() as con:
            con.execute("DELETE FROM documents WHERE path=? AND page=?", (path, page))
            con.execute("DELETE FROM documents_fts WHERE path=? AND page=?", (path, str(page)))
            cur = con.execute(
                "INSERT INTO documents(path, page, text) VALUES (?, ?, ?)",
                (path, page, content),
            )
            con.execute(
                "INSERT INTO documents_fts(rowid, path, page, text) VALUES (?, ?, ?, ?)",
                (cur.lastrowid, path, str(page), content),
            )

    def remove_file(self, path):
        with self.connect() as con:
            con.execute("DELETE FROM documents WHERE path=?", (path,))
            con.execute("DELETE FROM documents_fts WHERE path=?", (path,))

    def search(self, query, limit=100):
        # Build a safe FTS expression from words; terms are combined with AND.
        import re
        terms = re.findall(r"[\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ-]+", query, flags=re.UNICODE)
        if not terms:
            return []
        expression = " AND ".join('"' + term.replace('"', '""') + '"' for term in terms)
        with self.connect() as con:
            rows = con.execute("""
                SELECT path, CAST(page AS INTEGER) AS page,
                       snippet(documents_fts, 2, '⟦', '⟧', ' … ', 18) AS excerpt,
                       bm25(documents_fts) AS rank
                FROM documents_fts
                WHERE documents_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (expression, limit)).fetchall()
        return [dict(row) for row in rows]

    def count_pages(self):
        with self.connect() as con:
            return con.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
