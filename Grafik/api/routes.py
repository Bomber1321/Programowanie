from flask import Blueprint, g, request, jsonify, abort
from db.init import get_db

api = Blueprint("api", __name__)


@api.route("/employees", methods=["GET"])
def api_list_employees():
    db = get_db()
    rows = db.execute("SELECT id, name, surname, positions, active, created_at FROM employees ORDER by created_at DESC").fetchall()
    return jsonify([dict(row) for row in rows])

@api.route("/employees/<int:employee_id>", methods=["GET"])
def api_employees_get(employee_id):
    db = get_db()
    row = db.execute("SELECT id, name, surname, positions, active, created_at FROM employees WHERE id = ?",[employee_id]).fetchone()

    if row is None:
        abort(404, description="Employee not found")
    
    return jsonify(dict(row))

@api.route("/employees", methods=["POST"])
def api_employee_add():
    db = get_db()
    data = request.get_json(silent=True)

    if not data or "name" not in data or "surname" not in data or "positions" not in data or "active" not in data:
        abort(400, description="Missing DATA")
        
    active = 1 if data["active"] == "active" else 0
    row = db.execute("INSERT INTO employees (name, surname, positions, active) VALUES (?, ?, ?, ?)",(data["name"],data["surname"],data["positions"], active))
    db.commit()
    return jsonify({
        "message": "Employee added successfully", 
        "id": row.lastrowid
    }), 201
    
@api.route("/employees/<int:employee_id>", methods=["PUT", "PATCH"])
def api_employee_update(employee_id):
    db = get_db()
    data = request.get_json(silent=True)

    if not data:
        abort(400, description="Missing DATA")

    # Check if employee exists
    employee = db.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
    if employee is None:
        abort(404, description="Employee not found")

    # Update employee details
    name = data.get("name", employee["name"])
    surname = data.get("surname", employee["surname"])
    positions = data.get("positions", employee["positions"])
    active = 1 if data.get("active") == "active" else 0

    db.execute("UPDATE employees SET name = ?, surname = ?, positions = ?, active = ? WHERE id = ?", (name, surname, positions, active, employee_id))
    db.commit()

    return jsonify({"message": "Employee updated successfully"})

@api.route("/employees/<int:employee_id>", methods=["DELETE"])
def api_employee_delete(employee_id):
    db = get_db()
    employee = db.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
    if employee is None:
        abort(404, description="Employee not found")
    
    db.execute("DELETE FROM availability WHERE id_employee = ?", (employee_id,))
    db.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
    db.commit()

    return jsonify({"message": "Employee deleted successfully"})

@api.route("/months", methods=["GET"])
def api_list_months():
    db = get_db()
    rows = db.execute("SELECT * FROM months").fetchall()
    return jsonify([dict(row) for row in rows])

@api.route("/months/<int:month_id>", methods=["GET"])
def api_months_get(month_id):
    db = get_db()
    row = db.execute("SELECT * FROM months WHERE id = ?",[month_id]).fetchone()

    if row is None:
        abort(404, description="Month not found")
    
    return jsonify(dict(row))

@api.route("/months", methods=["POST"])
def api_month_add():
    db = get_db()
    data = request.get_json(silent=True)

    if not data or "name" not in data or "length" not in data or "year" not in data or "weekday_start" not in data:
        abort(400, description="Missing DATA")
        
    if data["weekday_start"] not in ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota', 'Niedziela']:
        abort(400, description="Incorrect weekday_start")
        
    row = db.execute("INSERT INTO months (name, length, year, weekday_start) VALUES (?, ?, ?, ?)",(data["name"],data["length"],data["year"], data["weekday_start"]))
    db.commit()
    return jsonify({
        "message": "Month added successfully", 
        "id": row.lastrowid
    }), 201
    
@api.route("/months/<int:month_id>", methods=["PUT", "PATCH"])
def api_month_update(month_id):
    db = get_db()
    data = request.get_json(silent=True)

    if not data:
        abort(400, description="Missing DATA")

    month = db.execute("SELECT * FROM months WHERE id = ?", (month_id,)).fetchone()
    if month is None:
        abort(404, description="Month not found")

    name = data.get("name", month["name"])
    length = data.get("length", month["length"])
    year = data.get("year", month["year"])
    weekday_start = data.get("weekday_start", month["weekday_start"])

    if weekday_start not in ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota', 'Niedziela']:
        abort(400, description="Incorrect weekday_start")

    db.execute("UPDATE months SET name = ?, length = ?, year = ?, weekday_start = ? WHERE id = ?", (name, length, year, weekday_start, month_id))
    db.commit()

    return jsonify({"message": "Month updated successfully"})

@api.route("/months/<int:month_id>", methods=["DELETE"])
def api_month_delete(month_id):
    db = get_db()
    month = db.execute("SELECT * FROM months WHERE id = ?", (month_id,)).fetchone()
    if month is None:
        abort(404, description="Month not found")
    db.execute("DELETE FROM availability WHERE id_month = ?", (month_id,))
    db.execute("DELETE FROM calendar WHERE month_id = ?", (month_id,))
    db.execute("DELETE FROM months WHERE id = ?", (month_id,))
    db.commit()

    return jsonify({"message": "Month deleted successfully"})

@api.route("/positions", methods=["GET"])
def api_list_positions():
    db = get_db()
    rows = db.execute("SELECT * FROM positions").fetchall()
    return jsonify([dict(row) for row in rows])

@api.route("/positions/<int:position_id>", methods=["GET"])
def api_positions_get(position_id):
    db = get_db()
    row = db.execute("SELECT * FROM positions WHERE id = ?",[position_id]).fetchone()

    if row is None:
        abort(404, description="Position not found")
    
    return jsonify(dict(row))

@api.route("/positions", methods=["POST"])
def api_position_add():
    db = get_db()
    data = request.get_json(silent=True)

    if not data or "name" not in data:
        abort(400, description="Missing DATA")
        
    row = db.execute("INSERT INTO positions (name) VALUES (?)", (data["name"],))
    db.commit()
    return jsonify({
        "message": "Position added successfully", 
        "id": row.lastrowid
    }), 201
    
@api.route("/positions/<int:position_id>", methods=["PUT", "PATCH"])
def api_position_update(position_id):
    db = get_db()
    data = request.get_json(silent=True)

    if not data:
        abort(400, description="Missing DATA")

    position = db.execute("SELECT * FROM positions WHERE id = ?", (position_id,)).fetchone()
    if position is None:
        abort(404, description="Position not found")

    name = data.get("name", position["name"])

    db.execute("UPDATE positions SET name = ? WHERE id = ?", (name, position_id))
    db.commit()

    return jsonify({"message": "Position updated successfully"})
    
@api.route("/positions/<int:position_id>", methods=["DELETE"])
def api_position_delete(position_id):
    db = get_db()
    position = db.execute("SELECT * FROM positions WHERE id = ?", (position_id,)).fetchone()
    if position is None:
        abort(404, description="Position not found")
    db.execute("DELETE FROM required_employees WHERE position = ?", (position_id,))
    db.execute("DELETE FROM positions WHERE id = ?", (position_id,))
    db.commit()

    return jsonify({"message": "Position deleted successfully"})

@api.route("/required-employees", methods=["GET"])
def api_list_required_employees():
    db = get_db()
    rows = db.execute("SELECT * FROM required_employees").fetchall()
    return jsonify([dict(row) for row in rows])

@api.route("/required-employees/<int:required_employees_id>", methods=["GET"])
def api_required_employees_get(required_employees_id):
    db = get_db()
    row = db.execute("SELECT * FROM required_employees WHERE id = ?",[required_employees_id]).fetchone()

    if row is None:
        abort(404, description="Required employees row not found")
    
    return jsonify(dict(row))

@api.route("/required-employees", methods=["POST"])
def api_required_employees_add():
    db = get_db()
    data = request.get_json(silent=True)

    if not data or "weekday" not in data or "position" not in data or "required_count" not in data:
        abort(400, description="Missing DATA")
        
    row = db.execute("INSERT INTO required_employees (weekday, position, required_count) VALUES (?, ?, ?)",(data["weekday"],data["position"],data["required_count"]))
    db.commit()
    return jsonify({
        "message": "Required employees row added successfully", 
        "id": row.lastrowid
    }), 201
    
@api.route("/required-employees/<int:required_employees_id>", methods=["PUT", "PATCH"])
def api_required_employees_update(required_employees_id):
    db = get_db()
    data = request.get_json(silent=True)

    if not data:
        abort(400, description="Missing DATA")

    requirement = db.execute("SELECT * FROM required_employees WHERE id = ?", (required_employees_id,)).fetchone()
    if requirement is None:
        abort(404, description="Required employees row not found")

    weekday = data.get("weekday", requirement["weekday"])
    position = data.get("position", requirement["position"])
    required_count = data.get("required_count", requirement["required_count"])

    db.execute("UPDATE required_employees SET weekday = ?, position = ?, required_count = ? WHERE id = ?", (weekday, position, required_count, required_employees_id))
    db.commit()

    return jsonify({"message": "Required employees row updated successfully"})

@api.route("/required-employees/<int:required_employees_id>", methods=["DELETE"])
def api_required_employees_delete(required_employees_id):
    db = get_db()
    requirement = db.execute("SELECT * FROM required_employees WHERE id = ?", (required_employees_id,)).fetchone()
    if requirement is None:
        abort(404, description="Required employees row not found")

    db.execute("DELETE FROM required_employees WHERE id = ?", (required_employees_id,))
    db.commit()

    return jsonify({"message": "Required employees row deleted successfully"})

@api.route("/availability", methods=["GET"])
def api_list_availability():
    db = get_db()
    rows = db.execute("SELECT * FROM availability").fetchall()
    return jsonify([dict(row) for row in rows])

@api.route("/availability", methods=["POST"])
def api_availability_add():
    db = get_db()
    data = request.get_json(silent=True)

    if not data or "id_employee" not in data or "id_month" not in data or "day" not in data or "weekday" not in data or "available" not in data:
        abort(400, description="Missing DATA")
        
    available = 1 if data["available"] == "available" else 0
    row = db.execute("INSERT INTO availability (id_employee, id_month, day, weekday, available) VALUES (?, ?, ?, ?, ?)",(data["id_employee"],data["id_month"],data["day"],data["weekday"], available))
    db.commit()
    return jsonify({
        "message": "Availability row added successfully", 
        "id": row.lastrowid
    }), 201

@api.route("/availability/<int:availability_id>", methods=["GET"])
def api_availability_get(availability_id):
    db = get_db()
    row = db.execute("SELECT * FROM availability WHERE id = ?",[availability_id]).fetchone()

    if row is None:
        abort(404, description="Availability row not found")
    
    return jsonify(dict(row))

@api.route("/availability/<int:availability_id>", methods=["PUT", "PATCH"])
def api_availability_update(availability_id):
    db = get_db()
    data = request.get_json(silent=True)

    if not data:
        abort(400, description="Missing DATA")

    availability = db.execute("SELECT * FROM availability WHERE id = ?", (availability_id,)).fetchone()
    if availability is None:
        abort(404, description="Availability row not found")

    id_employee = data.get("id_employee", availability["id_employee"])
    id_month = data.get("id_month", availability["id_month"])
    day = data.get("day", availability["day"])
    weekday = data.get("weekday", availability["weekday"])
    available = 1 if data.get("available") == "available" else 0

    db.execute("UPDATE availability SET id_employee = ?, id_month = ?, day = ?, weekday = ?, available = ? WHERE id = ?", (id_employee, id_month, day, weekday, available, availability_id))
    db.commit()

    return jsonify({"message": "Availability row updated successfully"})

@api.route("/availability/<int:availability_id>", methods=["DELETE"])
def api_availability_delete(availability_id):
    db = get_db()
    availability = db.execute("SELECT * FROM availability WHERE id = ?", (availability_id,)).fetchone()
    if availability is None:
        abort(404, description="Availability row not found")

    db.execute("DELETE FROM availability WHERE id = ?", (availability_id,))
    db.commit()

    return jsonify({"message": "Availability row deleted successfully"})

