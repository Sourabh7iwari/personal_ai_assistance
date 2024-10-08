import spacy

nlp = spacy.load('en_core_web_sm')

def parse_task(input_text):
    doc = nlp(input_text)
    # Improve this based on your NLP needs, e.g., intent detection, extracting dates, etc.
    tasks = [ent.text for ent in doc.ents]
    return tasks
