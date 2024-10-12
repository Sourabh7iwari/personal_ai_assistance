from apscheduler.schedulers.background import BackgroundScheduler
from task_manager import fetch_tasks
import datetime

scheduler = BackgroundScheduler()

def check_reminders():
    now = datetime.datetime.now()
    tasks = fetch_tasks()
    for task in tasks:
        if task[2] and task[2] <= now: 
            print(f"Reminder: {task[1]} is due soon!") 

scheduler.add_job(check_reminders, 'interval', minutes=30)
def start_scheduler():
    if not scheduler.running:
        scheduler.start()
