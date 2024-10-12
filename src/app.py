from flask import Flask, request, jsonify
from src.task_manager import add_task, fetch_tasks, remove_task, mark_task_done
from src.nlp_engine import parse_task
from src.reminder_scheduler import start_scheduler
from datetime import timedelta

app = Flask(__name__)

@app.route('/add_task', methods=['POST'])
def add_task_route():
    data = request.json
    task_name = data['task_name']
    due_date = data['due_date']
    reminder_time = data['reminder_time']
    add_task(task_name, due_date, reminder_time)
    return jsonify({'message': 'Task added successfully!'})

@app.route('/get_tasks', methods=['GET'])
def get_tasks_route():
    tasks = fetch_tasks()
    return jsonify(tasks)

@app.route('/process_task', methods=['POST'])
def process_task_route():
    input_text = request.json['input_text']
    task_name, due_date, priority, recurrence = parse_task(input_text)

    if task_name:
        reminder_time = None
        if due_date:
            reminder_time = due_date - timedelta(hours=2)  # Default reminder 2 hours before due date
        
        return(add_task(task_name, due_date, reminder_time, priority, recurrence))
        
    else:
        return jsonify({'error': 'Unable to parse task or due date'}), 400

@app.route('/delete_task/<int:task_id>', methods=['DELETE'])
def delete_task_route(task_id):
    return remove_task(task_id)

@app.route('/mark_done/<int:task_id>', methods=['POST'])
def mark_task_done_route(task_id):
    return mark_task_done(task_id)


if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True)
