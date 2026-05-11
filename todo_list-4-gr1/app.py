from flask import Flask, render_template, g, redirect, url_for, flash, request, jsonify, abort
import secrets
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
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
    howManyTasks = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if howManyTasks == 0:
        db.executemany("INSERT INTO tasks(title, done) VALUES (?, ?)",
                       [["Śniadanie", 1], ["Wyjść po mleko", 0], ["Zmywać naczynia", 0]])
        db.commit()
        print("✔ Dane przykładowe zostały dodane do tabeli tasks.")
    else:
        print("❌ Tabela tasks zawiera już dane, seedowanie przerwane.")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ping-db")
def ping_db():
    db = get_db()
    db.execute("SELECT 1").fetchone()
    return render_template("ping.html")

@app.route("/list_tasks")
def list_tasks():
    db = get_db()
    tasks = db.execute("SELECT id, title, done, created_at FROM tasks ORDER BY created_at DESC").fetchall()
    return render_template("list_tasks.html", tasks=tasks)

@app.route("/task/<int:task_id>")
def task(task_id):
    db = get_db()
    task = db.execute("SELECT id, title, done, created_at FROM tasks WHERE id = ?", [task_id]).fetchone()
    return render_template("task.html", task=task)

@app.route("/add_task",  methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        title = request.form.get("title")
        if len(title) < 3:
            flash("tytuł musi mieć przynajmniej 3 znaki.")
            return render_template("add_task.html", title=title)
        db = get_db()
        existing_task = db.execute("SELECT id FROM tasks WHERE done = 0 AND title LIKE ?", [title]).fetchone()
        if existing_task:
            flash("Na liście znajduje się już zadanie o takim tytule, które nie jest zakończone.")
            return render_template("add_task.html", title=title)

        db.execute("INSERT INTO tasks(title, done) VALUES (?, ?)", [title, 0])
        db.commit()
        flash("Zadanie zostało dodane.")
        return redirect(url_for("list_tasks"))
    return render_template("add_task.html")

@app.route("/tasks/<int:task_id>/status", methods=["POST"])
def update_tasks_status(task_id):
    db = get_db()
    db.execute("UPDATE tasks SET done = NOT done WHERE id = ?", [task_id])
    db.commit()
    view_name = request.form.get("view_name")
    flash("Zaktualizowano status zadania.")
    if view_name == "task":
        return redirect(url_for("task", task_id = task_id))
    return redirect(url_for("list_tasks"))

@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ?", [task_id])
    db.commit()
    flash("Usunięto zadanie.")
    return redirect(url_for("list_tasks"))

@app.route("/tasks/<int:task_id>/title", methods=["POST"])
def update_task_title(task_id):
    title = request.form.get("title")
    if len(title) < 3:
        flash("tytuł musi mieć przynajmniej 3 znaki.")
        return redirect(url_for("task", task_id = task_id, title=title))
    db = get_db()
    existing_task = db.execute("SELECT id FROM tasks WHERE done = 0 AND title LIKE ?", [title]).fetchone()
    if existing_task:
        flash("Na liście znajduje się już zadanie o takim tytule, które nie jest zakończone.")
        return redirect(url_for("task", task_id = task_id, title=title))
    db.execute("UPDATE tasks SET title = ? WHERE id = ?", [title, task_id])
    db.commit()
    flash("Zmieniono tytuł zadania.")
    return redirect(url_for("task", task_id = task_id, title=None))

@app.route("/api/tasks", methods=["GET"])
def api_tasks_list():
    db = get_db()
    rows = db.execute("SELECT id, title, done, created_at FROM tasks ORDER BY created_at DESC").fetchall()
    return jsonify([dict(row) for row in rows])

@app.route("/api/tasks/<int:task_id>", methods=["GET"])
def api_tasks_get(task_id):
    db = get_db()
    row = db.execute("SELECT id, title, done, created_at FROM tasks WHERE id = ?", [task_id]).fetchone()

    if row is None:
        abort(404, description="Task not found")
    
    return jsonify(dict(row))

@app.route("/api/tasks", methods=["POST"])
def api_tasks_add():
    data = request.get_json(silent=True)

    if not data or "title" not in data:
        abort(400, description="Missing JSON or title")

    title = data["title"].strip()
    if len(title) < 3:
        abort(400, description="Title has to have at least 3 chars.")
    db = get_db()
    existing_task = db.execute("SELECT id FROM tasks WHERE done = 0 AND title LIKE ?", [title]).fetchone()
    if existing_task:
        abort(400, description="There is already unfinished task with this title.")

    done = 1 if data.get("done") else 0
    cur = db.execute("INSERT INTO tasks(title, done) VALUES (?, ?)", [title, done])
    db.commit()

    task_id = cur.lastrowid
    row = db.execute("SELECT id, title, done, created_at FROM tasks WHERE id = ?", [task_id]).fetchone()
    
    return jsonify(dict(row)), 201

if __name__ == "__main__":
    app.run(debug=True)