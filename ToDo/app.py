from flask import Flask, render_template, g, redirect, url_for, flash, request
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
    tasks = db.execute("SELECT id, title, done, created_at FROM tasks ORDER by created_at DESC").fetchall()
    return render_template("list_tasks.html", tasks=tasks)

@app.route("/add_task", methods=["GET","POST"])
def add_tasks():
    if request.method == "POST":
        title = request.form.get("title")
        if len(title) < 3:
            flash("Tytuł musi mieć przynajmniej 3 znaki")
            return render_template("add_task.html", title=title)
        db = get_db()
        existing_task=db.execute("SELECT id FROM tasks WHERE done = 0 AND title LIKE ?", [title]).fetchone()
        if existing_task:
            flash("na liście jest już takie zadanie")
            return render_template("add_task.html", title=title)
        db.execute("INSERT INTO tasks(title, done) VALUES (?, ?)", [title, 0])
        db.commit()
        flash("Zadanie zostało dodane")
        return redirect(url_for("list_tasks"))
    return render_template("add_task.html")

@app.route("/tasks/<int:task_id>/status", methods=["POST"])
def update_task_status(task_id):
    db = get_db()
    db.execute("UPDATE tasks SET done = NOT done where id=?", [task_id])
    db.commit()
    flash("Zaktualizowano zadanie")
    view_name = request.form.get("view_name")
    if view_name == "task":
        return redirect(url_for("task", task_id = task_id))
    return redirect(url_for("list_tasks"))

@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    db = get_db()
    db.execute("DELETE from tasks where id=?", [task_id])
    db.commit()
    flash("Usunieto zadanie")
    return redirect(url_for("list_tasks"))

@app.route("/tasks/<int:task_id>")
def task(task_id):
    db = get_db()
    task = db.execute("SELECT id, title, done, created_at FROM tasks WHERE id = ?", [task_id]).fetchone()
    return render_template("task.html", task = task)

@app.route("/tasks/<int:task_id>/title", methods=["POST"])
def update_task_title(task_id):
    title = request.form.get("title")
    db = get_db()
    if len(title) < 3:
        flash("Tytuł musi mieć przynajmniej 3 znaki")
        return redirect(url_for("task", task_id = task_id))
    db = get_db()
    existing_task=db.execute("SELECT id FROM tasks WHERE done = 0 AND title LIKE ?", [title]).fetchone()
    if existing_task:
        flash("na liście jest już takie zadanie")
        return redirect(url_for("task", task_id = task_id))
    db.execute("UPDATE tasks SET title = ? where id=?", [title, task_id])
    db.commit()
    flash("Zaktualizowano zadanie")
    view_name = request.form.get("view_name")
    return redirect(url_for("task", task_id = task_id))

if __name__ == "__main__":
    app.run(debug=True)