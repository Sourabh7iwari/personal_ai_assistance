from database import connect_db
from flask import jsonify


# new project addition
def check_duplicate_project(title):
    conn = connect_db()
    cursor = conn.cursor()

    # lower title of both to  avoid case sensitivity, hehe!
    normalized_title = title.strip().lower()

    cursor.execute("SELECT * FROM projects WHERE LOWER(title) = %s", (normalized_title,))
    existing_project = cursor.fetchone()

    cursor.close()
    conn.close()

    return existing_project is not None


def add_project(title, requirements):
    # Check for duplicate project, if i get same idea again and i forgot that this  project already going, i'm dumb otherwise i wouldn't have needed you (this AI assistance )
    if check_duplicate_project(title):
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
