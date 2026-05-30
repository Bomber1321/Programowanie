import sqlite3
from flask import g

DATABASE = "todo.db"
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tasks(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT NOT NULL,
done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1)),
created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks(done);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
"""

def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        g.db = conn
    return g.db

def close_db_init(app):
    @app.teardown_appcontext
    def close_db(exception):
        db = g.pop("db", None)
        if db is not None:
            db.close()

def init_db():
    db = get_db()
    db.executescript(SCHEMA_SQL)
    db.commit()

def init_db_command_init(app):
    @app.cli.command("init-db")
    def init_db_command():
        init_db()
        print("✔ Zainicjowano bazę danych")

def seed_db_command_init(app):
    @app.cli.command("seed-db")
    def seed_db_command():
        db = get_db()
        howManyTasks = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if howManyTasks == 0:
            db.executemany("INSERT INTO tasks(title, done) VALUES (?, ?)",
                        [["Śniadanie", 1], ["Wyjść po mleko", 0], ["Zmywać naczynia", 0]])
            db.commit()
            print("✔ Dane przykładowe zostały dodane do tabeli tasks.")
        else:
            print("❌ Tabela tasks zawiera już dane, seedowanie przerwane.")