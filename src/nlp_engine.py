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
                input_text = input_text.lower().replace(phrase.lower(), '').strip()

    for ent in doc.ents:
        if ent.label_ == "DATE":
            if "tomorrow" in ent.text:
                due_date = datetime.now() + timedelta(days=1)
            else:
                due_date = dateparser.parse(ent.text)
                print(due_date)
            
            task_name = input_text.replace(ent.text, '').strip()


    if recurrence and due_date is None:
        if recurrence == 'daily':
            due_date = datetime.now() + timedelta(days=1)  
        elif recurrence == 'weekly':
            due_date = datetime.now() + timedelta(weeks=1) 
        elif recurrence == 'monthly':
            due_date = datetime.now() + timedelta(weeks=4) 

    if not task_name:
        task_name = input_text.strip()

    return task_name, due_date, priority, recurrence

def parse_project_command(input_text):
    """
    Parse the user input to detect project commands, project name, requirements, or steps.
    """
    doc = nlp(input_text)

    # Debugging: Print out detected entities and token structure
    print(f"Entities found: {[ (ent.text, ent.label_) for ent in doc.ents ]}")
    for token in doc:
        print(f"Token: {token.text}, POS: {token.pos_}, Dependency: {token.dep_}")

    project_name = None
    requirements = None
    step = None
    command_type = None

    # Detect command intent based on verbs
    for token in doc:
        if token.pos_ == "VERB":
            if token.lemma_ in ["create", "start", "begin"]:
                command_type = "create_project"
            elif token.lemma_ in ["add", "include"]:
                command_type = "add_step"
            elif token.lemma_ in ["complete", "finish", "delete"]:
                command_type = "complete_project"
            elif token.lemma_ in ["check", "see", "monitor"]:
                command_type = "check_status"

    # Extract the project name and requirements using NLP entities and dependency parsing
    project_name = extract_project_name(doc)
    requirements = extract_requirements(doc)

    # Optionally, extract steps (if the command relates to steps)
    for ent in doc.ents:
        if ent.label_ in ["EVENT", "WORK_OF_ART"]:
            step = ent.text  # Example: "Implement the backend API"

    return command_type, project_name, requirements, step


def extract_project_name(doc):
    """
    Extract project name using entity recognition and dependency parsing.
    """
    project_name = None

    # First, try to detect project name using common entity labels
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART", "EVENT"]:
            project_name = ent.text
            print(f"Project name detected by entity: {project_name}")
            break

    # Fallback: Use noun chunks to extract noun phrases that include "project"
    if not project_name:
        for chunk in doc.noun_chunks:
            if "project" in chunk.text.lower():
                project_name = chunk.text.replace("project", "").strip()
                print(f"Project name detected by noun chunk: {project_name}")
                break

    # Fallback: Use dependency parsing to look for proper nouns and other related nouns
    if not project_name:
        for token in doc:
            if token.dep_ in ["compound", "nsubj", "attr"] and token.head.pos_ == "NOUN":
                project_name = " ".join([child.text for child in token.subtree])
                print(f"Project name detected by dependency parsing: {project_name}")
                break

    return project_name


def extract_requirements(doc):
    """
    Extract project requirements using noun chunks and dependency parsing.
    """
    requirements = None

    # Look for noun phrases that are listed as part of requirements
    # Example: "with requirements: NLP, Task Manager, and Reminder system"
    for token in doc:
        if token.text.lower() == "requirements" and token.dep_ == "pobj":
            requirements = []
            for right in token.rights:
                if right.pos_ == "NOUN" or right.pos_ == "PROPN":
                    requirements.append(right.text)
            if requirements:
                print(f"Requirements detected: {', '.join(requirements)}")
                return ", ".join(requirements)

    # Fallback: Look for list of nouns or noun phrases that might represent requirements
    if not requirements:
        requirements = [chunk.text for chunk in doc.noun_chunks if chunk.root.pos_ == "NOUN"]
        if requirements:
            print(f"Requirements detected by noun chunks: {', '.join(requirements)}")
            return ", ".join(requirements)

    return None
