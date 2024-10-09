from apscheduler.schedulers.background import BackgroundScheduler
from task_manager import fetch_tasks
import datetime

scheduler = BackgroundScheduler()

def check_reminders():
    now = datetime.datetime.now()
    tasks = fetch_tasks()
    for task in tasks:
        if task[2] and task[2] <= now:  # Check if reminder time is due
            print(f"Reminder: {task[1]} is due soon!")  # Trigger reminder (or send notification)

# Schedule the reminder checks every minute
scheduler.add_job(check_reminders, 'interval', minutes=1)
def start_scheduler():
    # Ensure this function is called only once
    if not scheduler.running:
        scheduler.start()
