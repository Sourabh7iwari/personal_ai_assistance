import spacy
from datetime import datetime, timedelta
import dateparser

nlp = spacy.load('en_core_web_sm')

def parse_task(input_text):
    doc = nlp(input_text)
    
    print(f"Entities found: {[ (ent.text, ent.label_) for ent in doc.ents ]}")

    task_name = None
    due_date = None
    priority = "normal"
    recurrence = None  

    priority_keywords = {
        "high": ["high priority", "urgent", "asap", "immediately", "important"],
        "low": ["low priority", "whenever", "no rush"]
    }


    recurrence_patterns = {
        "daily": ["every day", "daily"],
        "weekly": ["every week", "weekly", "every Monday", "every Tuesday"],
        "monthly": ["every month", "monthly"]
    }

    for key, phrases in priority_keywords.items():
        for phrase in phrases:
            if phrase.lower() in input_text.lower():
                priority = key
                input_text = input_text.lower().replace(phrase, '').strip() 

    for key, phrases in recurrence_patterns.items():
        for phrase in phrases:
            if phrase.lower() in input_text.lower():
                recurrence = key
                input_text = input_text.lower().replace(phrase.lower(), '').strip()  # Remove recurrence phrase

    for ent in doc.ents:
        if ent.label_ == "DATE":
            if "tomorrow" in ent.text:
                due_date = datetime.now() + timedelta(days=1)
            else:
                due_date = dateparser.parse(ent.text)
                print(due_date)
            
            task_name = input_text.replace(ent.text, '').strip()


    if recurrence and due_date is None:
        # Set the due date for recurring tasks based on current time
        if recurrence == 'daily':
            due_date = datetime.now() + timedelta(days=1)  # Due tomorrow
        elif recurrence == 'weekly':
            due_date = datetime.now() + timedelta(weeks=1)  # Due next week
        elif recurrence == 'monthly':
            due_date = datetime.now() + timedelta(weeks=4)  # Due next month


    if not task_name:
        task_name = input_text.strip()

    return task_name, due_date, priority, recurrence
