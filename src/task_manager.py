from database import connect_db

def add_task(task_name, due_date, reminder_time):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO public.tasks (task_name, due_date, reminder_time) VALUES (%s, %s, %s)",
            (task_name, due_date, reminder_time)
        )
        conn.commit()
    except Exception as e:
        print(f"Error occurred: {e}")
        conn.rollback()

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
