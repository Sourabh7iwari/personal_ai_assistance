from flask import Flask, request, jsonify
from src.task_manager import add_task, fetch_tasks, remove_task, mark_task_done
from src.nlp_engine import parse_task
from src.reminder_scheduler import start_scheduler
from datetime import timedelta
from project_manager import add_project, add_step, complete_step, get_project_details, list_projects


app = Flask(__name__)


"""Task and reminder API's, reminder are managed according to task type and time"""

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



"""Project API Endpoints to make, manage and discover  projects"""

@app.route('/add_project', methods=['POST'])
def add_project_route():
    data = request.json
    title = data['title']
    requirements = data.get('requirements', '')
    return add_project(title, requirements)


@app.route('/add_step', methods=['POST'])
def add_step_route():
    data = request.json
    project_id = data['project_id']
    step_description = data['step_description']
    return add_step(project_id, step_description)

# Route to mark a step as complete
@app.route('/complete_step/<int:step_id>', methods=['POST'])
def complete_step_route(step_id):
    return complete_step(step_id)

# Route to get details of a project along with steps and progress
@app.route('/get_project/<int:project_id>', methods=['GET'])
def get_project_route(project_id):
    return get_project_details(project_id)

# Route to list all projects
@app.route('/list_projects', methods=['GET'])
def list_projects_route():
    return list_projects()



if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True)
