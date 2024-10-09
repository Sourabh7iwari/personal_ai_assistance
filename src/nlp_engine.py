from datetime import datetime, timedelta
import spacy

nlp = spacy.load('en_core_web_sm')

def parse_task(input_text):
    doc = nlp(input_text)
    
    # Debugging: Print the recognized entities
    print(f"Entities found: {[ (ent.text, ent.label_) for ent in doc.ents ]}")

    task_name = None
    due_date = None

    # Loop through entities to extract due date and task name
    for ent in doc.ents:
        if ent.label_ == "DATE":
            # Convert "tomorrow" to actual date
            if "tomorrow" in ent.text:
                due_date = datetime.now() + timedelta(days=1)
            else:
                due_date = ent.text  # Keep the recognized date text for now
            
            # Assume everything before the DATE is part of the task name
            task_name = input_text.replace(ent.text, '').strip()

    return task_name, due_date
