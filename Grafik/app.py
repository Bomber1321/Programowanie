from flask import Flask, render_template, g, redirect, url_for, flash, request
import secrets
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
DATABASE = "todo.db"
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

CREATE TABLE if NOT EXISTS months(
id INTEGER PRIMARY KEY AUTOINCREMENT,
length INTEGER NOT NULL,
weekday_start TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS availability(
id INTEGER PRIMARY KEY AUTOINCREMENT,
id_employee INTEGER NOT NULL,
id_month INTEGER NOT NULL,
day INTEGER NOT NULL,
available INTEGER NOT NULL DEFAULT 0 CHECK (available IN (0, 1)),
FOREIGN KEY(id_employee) REFERENCES employees(id),
FOREIGN KEY(id_month) REFERENCES months(id)
);
"""

def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        g.db = conn
    return g.db



@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.executescript(SCHEMA_SQL)
    db.commit()

@app.cli.command("init-db")
def init_db_command():
    init_db()
    print("✔ Zainicjowano bazę danych")
    
@app.cli.command("seed-db")
def seed_db_command():
    db = get_db()
    howManyEmployees = db.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    if howManyEmployees == 0:
        db.executemany("INSERT INTO employees(name, surname, positions, active) VALUES (?, ?, ?, ?)",
                       [["Norbert", "Czerw", '{"main_position": "Kelner", "other_positions": ["Kierowca", "Barman"]}', 1],
                        ["Joanna", "Czerw", '{"main_position": "Barman", "other_positions": ["Kierowca", "Pizzer"]}', 1],
                        ["Mateusz", "Cieślik", '{"main_position": "Pizzer", "other_positions": ["Kierowca", "Kelner"]}', 1],
                        ["Daria", "Rogala", '{"main_position": "Pizzer", "other_positions": ["None"]}', 1],
                        ["Paulina", "Smusz", '{"main_position": "Pizzer", "other_positions": ["None"]}', 1],
                        ["Wiktoria", "Kisielewska", '{"main_position": "Barman", "other_positions": ["Kelner", "Pizzer"]}', 1],
                        ["Zuzanna", "Adamska", '{"main_position": "Kelner", "other_positions": ["Barman"]}', 1],
                        ["Jakub", "Kura", '{"main_position": "Kierowca", "other_positions": ["Kelner","Pizzer"]}', 1]])
        db.commit()
        print("✔ Dane przykładowe zostały dodane do tabeli employees.")
    else:
        print("❌ Tabela employees zawiera już dane, seedowanie przerwane.")
        
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ping-db")
def ping_db():
    db = get_db()
    db.execute("SELECT 1").fetchone()
    return render_template("ping.html")

@app.route("/list_employees")
def list_employees():
    db = get_db()
    employees = db.execute("SELECT id, name, surname, positions, active, created_at FROM employees ORDER by created_at DESC").fetchall()
    return render_template("list_employees.html", employees=employees)

if __name__ == "__main__":
    app.run(debug=True)