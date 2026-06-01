import sqlite3
from flask import g

DATABASE = "grafik.db"
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS employees(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
surname TEXT NOT NULL,
positions TEXT not null,
active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_employees_active ON employees(active);
CREATE INDEX IF NOT EXISTS idx_employees_created_at ON employees(created_at);


CREATE TABLE IF NOT EXISTS availability(
id INTEGER PRIMARY KEY AUTOINCREMENT,
id_employee INTEGER NOT NULL,
id_month INTEGER NOT NULL,
day INTEGER NOT NULL,
weekday TEXT NOT NULL,
available INTEGER NOT NULL DEFAULT 0 CHECK (available IN (0, 1)),
FOREIGN KEY(id_employee) REFERENCES employees(id),
FOREIGN KEY(id_month) REFERENCES months(id)
);

CREATE TABLE IF NOT EXISTS months (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    length INTEGER NOT NULL,
    weekday_start TEXT NOT NULL,
    year INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS calendar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month_id INTEGER NOT NULL,
    day_index INTEGER NOT NULL,
    weekday TEXT NOT NULL,
    available INTEGER DEFAULT 0 CHECK (available IN (0, 1)),
    FOREIGN KEY (month_id) REFERENCES months (id)
);

CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

create TABLE IF NOT EXISTS required_employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    weekday TEXT NOT NULL,
    position INTEGER NOT NULL,
    required_count INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (position) REFERENCES positions(id)
    )
"""
def SEED_SQL():
    db = get_db()
    seed_employees = db.executemany("INSERT INTO employees(name, surname, positions, active) VALUES (?, ?, ?, ?)",
    [["Marcin", "Nowak", 'Kelner', 1],
    ["Adrian", "Nowak", 'Barman', 1],
    ["Mateusz", "Kowalski", 'Pizzer', 1],
    ["Ewa", "Nowak", 'Pizzer', 1],
    ["Małgorzata", "Wiśniewska", 'Pizzer', 1],
    ["Wiktoria", "Kowalska", 'Barman', 1],
    ["Mariola", "Wójcik", 'Kelner', 1],
    ["Kacper", "Wójcik", 'Kierowca', 1]])
    
    seed_positions = db.executemany("INSERT INTO positions(name) VALUES (?)",
    [["Pizzer"], ["Barman"], ["Kelner"], ["Kierowca"]])
    
    seed_required_employees = db.executemany("INSERT INTO required_employees(weekday, position, required_count) VALUES (?, ?, ?)",
    [["Poniedziałek", 1, 2],
    ["Poniedziałek", 2, 1],
    ["Poniedziałek", 3, 2],
    ["Poniedziałek", 4, 1],
    ["Wtorek", 1, 2],
    ["Wtorek", 2, 1],
    ["Wtorek", 3, 2],
    ["Wtorek", 4, 1],
    ["Środa", 1, 2],
    ["Środa", 2, 1],
    ["Środa", 3, 2],
    ["Środa", 4, 1],
    ["Czwartek", 1, 2],
    ["Czwartek", 2, 1],
    ["Czwartek", 3, 2],
    ["Czwartek", 4, 1],
    ["Piątek", 1, 3],
    ["Piątek", 2, 2],
    ["Piątek", 3, 3],
    ["Piątek", 4, 2],
    ["Sobota", 1, 3],
    ["Sobota", 2, 2],
    ["Sobota", 3, 3],
    ["Sobota", 4, 2],
    ["Niedziela", 1, 3],
    ["Niedziela", 2, 2],
    ["Niedziela", 3, 3],
    ["Niedziela", 4, 2]])
    
    return 0


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
        isDatabaseEmpty = db.execute("SELECT COUNT(*) FROM employees").fetchone()[0] + db.execute("SELECT COUNT(*) FROM positions").fetchone()[0] + db.execute("SELECT COUNT(*) FROM required_employees").fetchone()[0]
        if isDatabaseEmpty == 0:
            SEED_SQL()
            db.commit()
            print("✔ Dane przykładowe zostały dodane do tabel.")
        else:
            print("❌ Tabele zawierają już dane, seedowanie przerwane.")
        