from database import connect_db
from flask import jsonify
from datetime import timedelta, datetime

def check_duplicate_task(task_name):
    conn = connect_db()
    cursor = conn.cursor()
    
    # Check if a task with the same name already exists
    cursor.execute(
        "SELECT * FROM tasks WHERE task_name = %s",
        (task_name,)
    )
    existing_task = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return existing_task is not None

def add_task(task_name, due_date, reminder_time, priority='normal', recurrence=None):
    conn = connect_db()
    cursor = conn.cursor()

    if check_duplicate_task(task_name):
        return jsonify({
            'message': f'Task "{task_name}" already exists.'
        })
    else:
        try:
            # Insert task with the additional priority and recurrence fields
            cursor.execute(
                """
                INSERT INTO tasks (task_name, due_date, reminder_time, priority, recurrence)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (task_name, due_date, reminder_time, priority, recurrence)
            )
            conn.commit()
            return jsonify({
                'message': f'Task "{task_name}" added with due date {due_date}, priority {priority}, and recurrence {recurrence}'
            })
        except Exception as e:
            print(f"Error occurred: {e}")
            conn.rollback()
            return jsonify({'error': 'Failed to add task. Please try again.'}), 500
        finally:
            # Ensure cursor and connection are always closed
            cursor.close()
            conn.close()

def remove_task(task_id):
    conn = connect_db()
    cursor = conn.cursor()

    # Try to delete the task based on the provided task_id
    try:
        cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        if cursor.rowcount > 0:
            conn.commit()
            return jsonify({'message': f'Task with ID {task_id} deleted successfully!'})
        else:
            return jsonify({'error': f'Task with ID {task_id} not found!'}), 404
    except Exception as e:
        print(f"Error occurred: {e}")
        conn.rollback()
        return jsonify({'error': 'Failed to delete task. Please try again.'}), 500
    finally:
        cursor.close()
        conn.close()


def mark_task_done(task_id):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Get the task details to check if it's recurring
        cursor.execute("SELECT task_name, due_date, reminder_time, priority, recurrence FROM tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()

        if not task:
            return jsonify({'error': f'Task with ID {task_id} not found!'}), 404

        task_name, due_date, reminder_time, priority, recurrence = task
        
        # If the task is not recurring, mark it as done and remove it
        if recurrence is None:
            remove_task(task_id)
            return jsonify({'message': f'"{task_name}" completed and removed from task list'})

        # Calculate the next due date based on recurrence
        next_due_date = None
        if recurrence == 'daily':
            next_due_date = datetime.now() + timedelta(days=1)
        elif recurrence == 'weekly':
            next_due_date = datetime.now() + timedelta(weeks=1)
        elif recurrence == 'monthly':
            next_due_date = datetime.now() + timedelta(weeks=4)  # Approximation

        # Calculate the next reminder time (2 hours before the next due date)
        next_reminder_time = next_due_date - timedelta(hours=2)

        # Mark the task as done temporarily and update with the next occurrence details
        cursor.execute(
            """
            UPDATE tasks
            SET done = FALSE, due_date = %s, reminder_time = %s
            WHERE id = %s
            """,
            (next_due_date, next_reminder_time, task_id)
        )
        conn.commit()

        return jsonify({
            'message': f'Task with ID {task_id} marked as done. Next instance scheduled with due date {next_due_date}.'
        })

    except Exception as e:
        print(f"Error occurred: {e}")
        conn.rollback()
        return jsonify({'error': 'Failed to mark task as done.'}), 500
    finally:
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
