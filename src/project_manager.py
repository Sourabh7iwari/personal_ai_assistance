from database import connect_db
from flask import jsonify


def get_project_id_by_name(project_name):
    """
    Helper function to get project ID based on the project name.
    """
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM projects WHERE LOWER(title) = %s", (project_name.lower(),))
    project = cursor.fetchone()

    cursor.close()
    conn.close()

    if project:
        return project[0]  # Return project ID
    return None



# new project addition
def project_exists(title=None, project_id=None):
    conn = connect_db()
    cursor = conn.cursor()
    print("got title")
    if title:
        # Normalize the title (lowercase, strip whitespace) for consistent comparison
        normalized_title = title.strip().lower()
        cursor.execute("SELECT * FROM projects WHERE LOWER(title) = %s", (normalized_title,))
    elif project_id:
        cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
    else:
        return False  # If neither title nor project_id is provided, return False.

    project = cursor.fetchone()

    cursor.close()
    conn.close()

    return project is not None  # Returns True if the project exists by title or ID


def add_project(title, requirements):
    # Check if the project already exists by title
    if project_exists(title=title):
        return jsonify({'message': f'Project "{title}" already exists.'}), 400

    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO projects (title, requirements) VALUES (%s, %s) RETURNING id",
            (title, requirements)
        )
        project_id = cursor.fetchone()[0]
        conn.commit()
        return jsonify({'message': f'Project "{title}" added successfully!', 'project_id': project_id})
    except Exception as e:
        conn.rollback()
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Failed to add project. Please try again.'}), 500
    finally:
        cursor.close()
        conn.close()


"""
    Step to a project addition (will work around how to add step with project(title, requi...) also later), 
    Right now we have to add step explicitly to project after project creation.
"""
def add_step(project_id, step_description):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO steps (project_id, step_description) VALUES (%s, %s)",
            (project_id, step_description)
        )
        conn.commit()
        return jsonify({'message': f'Step added to project ID {project_id}.'})
    except Exception as e:
        conn.rollback()
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Failed to add step. Please try again.'}), 500
    finally:
        cursor.close()
        conn.close()

# Mark step as complete
def complete_step(step_id):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE steps SET completed = TRUE WHERE id = %s", (step_id,))
        conn.commit()

        # Update project progress
        cursor.execute("""
            SELECT project_id, COUNT(*) AS total_steps, SUM(CASE WHEN completed THEN 1 ELSE 0 END) AS completed_steps
            FROM steps WHERE project_id = (SELECT project_id FROM steps WHERE id = %s) GROUP BY project_id
        """, (step_id,))
        result = cursor.fetchone()
        project_id, total_steps, completed_steps = result

        progress = (completed_steps / total_steps) * 100
        cursor.execute("UPDATE projects SET progress = %s WHERE id = %s", (progress, project_id))
        conn.commit()

        return jsonify({'message': f'Step {step_id} marked as complete! Project progress updated to {progress:.2f}%.'})
    except Exception as e:
        conn.rollback()
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Failed to complete step. Please try again.'}), 500
    finally:
        cursor.close()
        conn.close()

# Get project details along with steps and progress
def get_project_details(project_id):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
        project = cursor.fetchone()

        cursor.execute("SELECT * FROM steps WHERE project_id = %s", (project_id,))
        steps = cursor.fetchall()

        return jsonify({
            'project': {
                'id': project[0],
                'title': project[1],
                'requirements': project[2],
                'progress': project[3]
            },
            'steps': [{'id': step[0], 'description': step[2], 'completed': step[3]} for step in steps]
        })
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Failed to retrieve project details.'}), 500
    finally:
        cursor.close()
        conn.close()

# List all projects
def list_projects():
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM projects")
        projects = cursor.fetchall()
        return jsonify([{'id': project[0], 'title': project[1], 'progress': project[3]} for project in projects])
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Failed to retrieve projects.'}), 500
    finally:
        cursor.close()
        conn.close()

# project deletion section by checking if all steps completed or not
def check_project_completion(project_id):
    conn = connect_db()
    cursor = conn.cursor()

    # Check if all steps in the project are marked as completed
    cursor.execute("SELECT COUNT(*) FROM steps WHERE project_id = %s AND completed = FALSE", (project_id,))
    incomplete_steps_count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return incomplete_steps_count == 0  # Returns True if all steps are completed



def delete_project(project_id, force=False):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Check if the project exists
        if not project_exists(project_id=project_id):
            return jsonify({'error': f'Project with ID {project_id} not found!'}), 404

        # Check if the project has incomplete steps (if force is not used)
        if not check_project_completion(project_id) and not force:
            return jsonify({
                'message': 'Project has incomplete steps. Use force flag to delete anyway.'
            }), 400

        # Delete all steps related to the project
        cursor.execute("DELETE FROM steps WHERE project_id = %s", (project_id,))
        
        # Delete the project itself
        cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
        conn.commit()

        return jsonify({'message': f'Project with ID {project_id} deleted successfully!'})

    except Exception as e:
        conn.rollback()
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Failed to delete project.'}), 500
    finally:
        cursor.close()
        conn.close()
