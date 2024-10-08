from flask import Flask, request, jsonify
from task_manager import add_task, fetch_tasks
from nlp_engine import parse_task

app = Flask(__name__)

@app.route('/add_task', methods=['POST'])
def add_task_route():
    data = request.json
    task_name = data['task_name']
    due_date = data['due_date']
    reminder_time = data['reminder_time']
    add_task(task_name, due_date, reminder_time)
    return jsonify({'message': 'Task added successfully!'})

if __name__ == '__main__':
    app.run(debug=True)
