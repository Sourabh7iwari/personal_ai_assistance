from database import connect_db

def add_task(task_name, due_date, reminder_time):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (task_name, due_date, reminder_time) VALUES (%s, %s, %s)",
        (task_name, due_date, reminder_time)
    )
    conn.commit()
    cursor.close()
    conn.close()

def fetch_tasks():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    return tasks
