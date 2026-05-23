import json

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


CREATE TABLE IF NOT EXISTS availability(
id INTEGER PRIMARY KEY AUTOINCREMENT,
id_employee INTEGER NOT NULL,
id_month INTEGER NOT NULL,
day INTEGER NOT NULL,
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

@app.route("/add_month", methods=["GET", "POST"])
def add_month():
    db = get_db()
    cursor = db.cursor() # Use a cursor so we can get the lastrowid

    if request.method == "POST":
        month_name = request.form.get("month")
        month_length = int(request.form.get("month_length"))
        first_day = request.form.get("first_day")
        year = int(request.form.get("year"))
        # 1. Insert into the main 'months' table
        cursor.execute("INSERT INTO months(name, length, weekday_start, year) VALUES (?, ?, ?, ?)", 
                       (month_name, month_length, first_day, year))
        
        # 2. Grab the ID of the month we just inserted
        # This is the crucial step to link the two tables together
        new_month_id = cursor.lastrowid 
        
        # 3. Calculate the days
        weekdays = ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota', 'Niedziela']
        
        try:
            start_index = weekdays.index(first_day.capitalize())
        except ValueError:
            start_index = 0
            
        # 4. Prepare a list of all the days to insert
        days_data = []
        for day_index in range(1, month_length + 1):
            current_weekday = weekdays[(start_index + day_index - 1) % 7]
            # Notice we are passing the new_month_id as the first value
            days_data.append((new_month_id, day_index, current_weekday, 1))
        
        # 5. Bulk insert all days into the master calendar table at once
        cursor.executemany("""
            INSERT INTO calendar (month_id, day_index, weekday, available) 
            VALUES (?, ?, ?, ?)
        """, days_data)
        
        # 6. Prepare a list of all the days to insert into the availability table for each employee
        employees = db.execute("SELECT id FROM employees").fetchall()
        availability_data = []
        for emp in employees:
            emp_id = emp['id']
            for day_index in range(1, month_length + 1):
                availability_data.append((emp_id, new_month_id, day_index, 0))  # Default to unavailable
        
        # 7. Bulk insert all availability records into the availability table at once
        cursor.executemany("""
            INSERT INTO availability (id_employee, id_month, day, available) 
            VALUES (?, ?, ?, ?)
        """, availability_data)

        db.commit()
        return redirect(url_for("add_month"))
        # Process the form data (e.g., save to database)
    
    if request.method == "GET":
        months = db.execute("SELECT * FROM months").fetchall()
    return render_template("add_month.html", months=months)

@app.route("/list_employees")
def list_employees():
    db = get_db()
    raw_employees = db.execute("SELECT id, name, surname, positions, active, created_at FROM employees ORDER by created_at DESC").fetchall()
    employees = []
    for emp in raw_employees:
        emp_data = dict(emp)
        
        if emp_data.get('positions'):
            try:
                emp_data['positions'] = json.loads(emp_data['positions'])
            except json.JSONDecodeError:
                emp_data['positions'] = {}
        else:
            emp_data['positions'] = {}
            
        employees.append(emp_data)
        
    return render_template("list_employees.html", employees=employees)

@app.route("/edit_employee/<int:employee_id>", methods=["GET","POST"])
def edit_employee(employee_id):
    db = get_db()    
    
    ### Obsługa POST - aktualizacja danych pracownika

    
    ### Pobranie aktualnych danych pracownika z bazy
    employee = db.execute("SELECT id, name, surname, positions, active, created_at FROM employees WHERE id = ?", (employee_id,)).fetchone()
    if employee is None:
        flash("Nie znaleziono pracownika o podanym ID.", "danger")
        return redirect(url_for("list_employees"))
    
    employee_data = dict(employee)
    if employee_data.get('positions'):
        try:
            employee_data['positions'] = json.loads(employee_data['positions'])
        except json.JSONDecodeError:
            employee_data['positions'] = {}
    else:
        employee_data['positions'] = {}
    
    return render_template("edit_employee.html", employee=employee_data)

@app.route("/edit_employee/<int:employee_id>/main_position", methods=["POST"])
def edit_employee_main_position(employee_id):
    db = get_db()
    new_main_position = request.form.get("main_position")
    
    if new_main_position not in ['Pizzer', 'Barman', 'Kelner', 'Kierowca']:
        flash("Nieprawidłowa pozycja główna.", "danger")
        return redirect(url_for("edit_employee", employee_id=employee_id))
    
    employee = db.execute("SELECT positions FROM employees WHERE id = ?", (employee_id,)).fetchone()
    if employee is None:
        flash("Nie znaleziono pracownika o podanym ID.", "danger")
        return redirect(url_for("list_employees"))
    
    try:
        positions_data = json.loads(employee['positions'])
    except json.JSONDecodeError:
        positions_data = {"main_position": "", "other_positions": []}
    
    positions_data['main_position'] = new_main_position
    updated_positions_json = json.dumps(positions_data)
    
    db.execute("UPDATE employees SET positions = ? WHERE id = ?", (updated_positions_json, employee_id))
    db.commit()
    
    flash("Główna pozycja została zaktualizowana.", "success")
    return redirect(url_for("edit_employee", employee_id=employee_id))

@app.route("/edit_employee/<int:employee_id>/active", methods=["POST"])
def edit_employee_active(employee_id):
    db = get_db()
    new_active_status = request.form.get("active")
    
    if new_active_status not in ['0', '1']:
        flash("Nieprawidłowy status aktywności.", "danger")
        return redirect(url_for("edit_employee", employee_id=employee_id))
    
    db.execute("UPDATE employees SET active = ? WHERE id = ?", (int(new_active_status), employee_id))
    db.commit()
    
    flash("Status aktywności został zaktualizowany.", "success")
    return redirect(url_for("edit_employee", employee_id=employee_id))

@app.route("/edit_employee/<int:employee_id>/other_positions", methods=["POST"])
def edit_employee_other_positions(employee_id):
    db = get_db()
    new_other_positions = request.form.getlist("other_positions")
    
    for pos in new_other_positions:
        if pos not in ['Pizzer', 'Barman', 'Kelner', 'Kierowca']:
            flash("Nieprawidłowa pozycja dodatkowa: {}".format(pos), "danger")
            return redirect(url_for("edit_employee", employee_id=employee_id))
    
    employee = db.execute("SELECT positions FROM employees WHERE id = ?", (employee_id,)).fetchone()
    if employee is None:
        flash("Nie znaleziono pracownika o podanym ID.", "danger")
        return redirect(url_for("list_employees"))
    
    try:
        positions_data = json.loads(employee['positions'])
    except json.JSONDecodeError:
        positions_data = {"main_position": "", "other_positions": []}
    
    positions_data['other_positions'] = new_other_positions
    updated_positions_json = json.dumps(positions_data)
    
    db.execute("UPDATE employees SET positions = ? WHERE id = ?", (updated_positions_json, employee_id))
    db.commit()
    
    flash("Pozycje dodatkowe zostały zaktualizowane.", "success")
    return redirect(url_for("edit_employee", employee_id=employee_id))

@app.route("/month/<int:month_id>/availability", methods=["GET", "POST"])
def month_availability(month_id):
    db = get_db()
    month_calendar = db.execute("SELECT * FROM calendar WHERE month_id = ?", (month_id,)).fetchone()
    month = db.execute("SELECT * FROM months WHERE id = ?", (month_id,)).fetchone()
    
    if month is None:
        flash("Nie znaleziono miesiąca o podanym ID.", "danger")
        return redirect(url_for("add_month"))
        


    calendar = db.execute("SELECT * FROM calendar WHERE month_id = ? ORDER BY day_index", (month_id,)).fetchall()
    employees = db.execute("SELECT id, active, name, surname FROM employees").fetchall()

    return render_template("month_availability.html", month_info=month, calendar=calendar, employees=employees)



if __name__ == "__main__":
    app.run(debug=True)