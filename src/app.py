from flask import Flask, request, jsonify
from src.task_manager import add_task, fetch_tasks, remove_task, mark_task_done
from src.nlp_engine import parse_task, parse_project_command
from src.reminder_scheduler import start_scheduler
from datetime import timedelta
from project_manager import add_project, add_step, complete_step, get_project_details, list_projects, delete_project, get_project_id_by_name


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

@app.route('/process_project', methods=['POST'])
def process_project_route():
    input_text = request.json['input_text']
    command_type, project_name, requirements, step = parse_project_command(input_text)

    # Ensure project_name is present for commands that need it
    if not project_name and command_type != "create_project":
        return jsonify({'error': 'Project name is required for this command.'}), 400

    if command_type == "create_project":
        # Create a new project
        return add_project(project_name, requirements)

    elif command_type == "add_step":
        # Get project ID by name
        project_id = get_project_id_by_name(project_name)
        if not project_id:
            return jsonify({'error': f'Project "{project_name}" not found.'}), 404

        # Add a step to the project
        return add_step(project_id, step)

    elif command_type == "complete_project":
        # Get project ID by name
        project_id = get_project_id_by_name(project_name)
        if not project_id:
            return jsonify({'error': f'Project "{project_name}" not found.'}), 404

        # Mark the project as complete (or delete it with completion check)
        force = request.args.get('force', 'false').lower() == 'true'
        return delete_project(project_id, force)

    elif command_type == "check_status":
        # Get project ID by name
        project_id = get_project_id_by_name(project_name)
        if not project_id:
            return jsonify({'error': f'Project "{project_name}" not found.'}), 404

        # Check the project details (status)
        return get_project_details(project_id)

    else:
        return jsonify({'error': 'Invalid command or project name not detected.'}), 400



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


@app.route('/complete_step/<int:step_id>', methods=['POST'])
def complete_step_route(step_id):
    return complete_step(step_id)


@app.route('/get_project/<int:project_id>', methods=['GET'])
def get_project_route(project_id):
    return get_project_details(project_id)


@app.route('/list_projects', methods=['GET'])
def list_projects_route():
    return list_projects()

@app.route('/delete_project/<int:project_id>', methods=['DELETE'])
def delete_project_route(project_id):
    # Check for the force flag in the request (optional, defaults to False)
    force = request.args.get('force', 'false').lower() == 'true'
    return delete_project(project_id, force)


if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True)
