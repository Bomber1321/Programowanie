from flask import Blueprint, g, request, jsonify, abort
from db.init import get_db
from db.repository import get_task, insert_tasks
from helpers import validate_title

api = Blueprint("api", __name__)

@api.route("/tasks", methods=["GET"])
def api_tasks_list():
    db = get_db()
    rows = db.execute("SELECT id, title, done, created_at FROM tasks ORDER BY created_at DESC").fetchall()
    return jsonify([dict(row) for row in rows])

@api.route("/tasks/<int:task_id>", methods=["GET"])
def api_tasks_get(task_id):
    row = get_task(task_id)

    if row is None:
        abort(404, description="Task not found")
    
    return jsonify(dict(row))

@api.route("/tasks", methods=["POST"])
def api_tasks_add():
    data = request.get_json(silent=True)

    if not data or "title" not in data:
        abort(400, description="Missing JSON or title")

    title = data["title"]
    title_validation = validate_title(title)
    if title_validation is not None:
        abort(400, description=title_validation)

    done = 1 if data.get("done") else 0
    row = insert_tasks([[title, done]])

    return jsonify(dict(row)), 201

@api.route("/tasks/<int:task_id>", methods=["PUT", "PATCH"])
def api_tasks_update(task_id):
    db = get_db()
    row = get_task(task_id)

    if row is None:
        abort(404, description="Task not found")

    data = request.get_json(silent=True)

    if not data:
        abort(400, "Missing JSON")

    title = data.get("title")
    done = data.get("done")

    if title is not None:
        title_validation = validate_title(title)
        if title_validation is not None:
            abort(400, description=title_validation)

        db.execute("UPDATE tasks SET title = ? WHERE id = ?", [title, task_id])
    
    if done is not None:
        db.execute("UPDATE tasks SET done = ? WHERE id = ?", [done, task_id])
    
    db.commit()

    updated_row = get_task(task_id)
    return jsonify(dict(updated_row))

@api.route("/tasks/<int:task_id>", methods=["DELETE"])
def api_tasks_delete(task_id):
    db = get_db()
    cur = db.execute("DELETE FROM tasks WHERE id = ?", [task_id])
    db.commit()

    if cur.rowcount == 0:
        abort(404, description="Task not found")

    return "", 204 
