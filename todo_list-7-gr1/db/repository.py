from db.init import get_db

def get_task(task_id):
    db = get_db()
    row = db.execute("SELECT id, title, done, created_at FROM tasks WHERE id = ?", [task_id]).fetchone()
    return row

def get_task_by_title(title):
    db = get_db()
    row = db.execute("SELECT id, title, done, created_at FROM tasks WHERE title = ?", [title]).fetchone()
    return row

def insert_tasks(tasks):
    db = get_db()
    cur = db.executemany("INSERT INTO tasks(title, done) VALUES (?, ?)", tasks)
    db.commit()

    return cur.fetchall()