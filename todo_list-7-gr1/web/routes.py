from flask import Blueprint, render_template, g, redirect, url_for, flash, request
from db.init import get_db
from db.repository import get_task, insert_tasks
from helpers import validate_title

web = Blueprint("web", __name__)

@web.route("/")
def index():
    return render_template("index.html")

@web.route("/ping-db")
def ping_db():
    db = get_db()
    db.execute("SELECT 1").fetchone()
    return render_template("ping.html")

@web.route("/list_tasks")
def list_tasks():
    db = get_db()
    tasks = db.execute("SELECT id, title, done, created_at FROM tasks ORDER BY created_at DESC").fetchall()
    return render_template("list_tasks.html", tasks=tasks)

@web.route("/task/<int:task_id>")
def task(task_id):
    task = get_task(task_id)
    return render_template("task.html", task=task)

@web.route("/add_task",  methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        title = request.form.get("title")
        title_validation = validate_title(title)
        if title_validation is not None:
            flash(title_validation)
            return render_template("add_task.html", title=title)

        insert_tasks([title, 0])
        flash("Zadanie zostało dodane.")
        return redirect(url_for("web.list_tasks"))
    return render_template("add_task.html")

@web.route("/tasks/<int:task_id>/status", methods=["POST"])
def update_tasks_status(task_id):
    db = get_db()
    db.execute("UPDATE tasks SET done = NOT done WHERE id = ?", [task_id])
    db.commit()
    view_name = request.form.get("view_name")
    flash("Zaktualizowano status zadania.")
    if view_name == "task":
        return redirect(url_for("web.task", task_id = task_id))
    return redirect(url_for("web.list_tasks"))

@web.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ?", [task_id])
    db.commit()
    flash("Usunięto zadanie.")
    return redirect(url_for("web.list_tasks"))

@web.route("/tasks/<int:task_id>/title", methods=["POST"])
def update_task_title(task_id):
    title = request.form.get("title")
    title_validation = validate_title(title)
    if title_validation is not None:
        flash(title_validation)
        return redirect(url_for("web.task", task_id = task_id, title=title))
    db = get_db()
    db.execute("UPDATE tasks SET title = ? WHERE id = ?", [title, task_id])
    db.commit()
    flash("Zmieniono tytuł zadania.")
    return redirect(url_for("web.task", task_id = task_id, title=None))
