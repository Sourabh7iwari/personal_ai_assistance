from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from datetime import datetime, timedelta
import dateparser
import torch
from typing import Tuple, Optional, List, Dict
import re

# Initialize models
intent_classifier = pipeline("zero-shot-classification")
ner_pipeline = pipeline("token-classification", model="Jean-Baptiste/roberta-large-ner-english")
text_classifier = pipeline("text-classification", model="facebook/bart-large-mnli")

class NLPEngine:
    def __init__(self):
        self.priority_keywords = {
            "high": ["high priority", "urgent", "asap", "immediately", "important", "critical"],
            "low": ["low priority", "whenever", "no rush", "when possible"]
        }
        self.recurrence_patterns = {
            "daily": ["every day", "daily", "each day"],
            "weekly": ["every week", "weekly", "each week"],
            "monthly": ["every month", "monthly", "each month"]
        }

    def extract_dates(self, text: str) -> Optional[datetime]:
        """Extract dates using both NER and pattern matching"""
        # First try NER
        ner_results = ner_pipeline(text)
        date_entities = [ent for ent in ner_results if ent['entity'].startswith('B-DATE')]
        
        if date_entities:
            date_text = date_entities[0]['word']
            parsed_date = dateparser.parse(date_text)
            if parsed_date:
                return parsed_date

        # Fallback to pattern matching for common cases
        if "tomorrow" in text.lower():
            return datetime.now() + timedelta(days=1)
        elif "next week" in text.lower():
            return datetime.now() + timedelta(weeks=1)
        
        # Try dateparser as last resort
        return dateparser.parse(text, settings={'PREFER_DATES_FROM': 'future'})

    def detect_priority(self, text: str) -> Tuple[str, str]:
        """Detect priority using both keyword matching and sentiment analysis"""
        text_lower = text.lower()
        
        # Direct keyword matching
        for priority, phrases in self.priority_keywords.items():
            for phrase in phrases:
                if phrase in text_lower:
                    return priority, text_lower.replace(phrase, '').strip()
        
        # Use text classification for sentiment/urgency detection
        priorities = ["urgent", "normal", "low priority"]
        result = text_classifier(text, priorities, multi_label=False)
        
        if result['scores'][0] > 0.6:  # High confidence threshold
            if result['labels'][0] == "urgent":
                return "high", text
            elif result['labels'][0] == "low priority":
                return "low", text
        
        return "normal", text

    def detect_recurrence(self, text: str) -> Tuple[Optional[str], str]:
        """Detect recurrence pattern using zero-shot classification"""
        text_lower = text.lower()
        
        # Direct pattern matching
        for pattern, phrases in self.recurrence_patterns.items():
            for phrase in phrases:
                if phrase in text_lower:
                    return pattern, text_lower.replace(phrase, '').strip()
        
        # Zero-shot classification for more flexible matching
        candidate_labels = ["daily task", "weekly task", "monthly task", "one-time task"]
        result = intent_classifier(text, candidate_labels)
        
        if result['scores'][0] > 0.7:  # High confidence threshold
            if "daily" in result['labels'][0]:
                return "daily", text
            elif "weekly" in result['labels'][0]:
                return "weekly", text
            elif "monthly" in result['labels'][0]:
                return "monthly", text
        
        return None, text

    def parse_task(self, input_text: str) -> Tuple[str, Optional[datetime], str, Optional[str]]:
        """Enhanced task parsing with transformer-based NLP"""
        # Clean input
        input_text = input_text.strip()
        
        # Extract priority first as it might contain important context
        priority, cleaned_text = self.detect_priority(input_text)
        
        # Extract recurrence pattern
        recurrence, cleaned_text = self.detect_recurrence(cleaned_text)
        
        # Extract date
        due_date = self.extract_dates(cleaned_text)
        
        # Extract task name by removing date expressions
        task_name = cleaned_text
        if due_date:
            # Remove date-related text using regex
            date_patterns = [
                r'\b(on|by|at|before|after)\s+\d{1,2}(st|nd|rd|th)?\s+\w+(\s+\d{4})?\b',
                r'\b\d{1,2}(st|nd|rd|th)?\s+\w+(\s+\d{4})?\b',
                r'\btomorrow\b',
                r'\bnext\s+\w+\b'
            ]
            for pattern in date_patterns:
                task_name = re.sub(pattern, '', task_name, flags=re.IGNORECASE)
        
        task_name = ' '.join(task_name.split())  # Clean up whitespace
        
        return task_name, due_date, priority, recurrence

    def parse_project_command(self, input_text: str) -> Tuple[str, Optional[str], Optional[List[str]], Optional[str]]:
        """Enhanced project command parsing using zero-shot classification"""
        # Define possible command types
        command_candidates = [
            "create new project",
            "start a new project",
            "start new project",
            "add step to project",
            "complete project",
            "check project status",
            "delete project"
        ]
        
        # Classify command type
        command_result = intent_classifier(input_text, command_candidates)
        command_label = command_result['labels'][0]
        print(f"DEBUG - All labels and scores:")
        for label, score in zip(command_result['labels'], command_result['scores']):
            print(f"  {label}: {score}")
        
        # Map command labels to command types
        if "create" in command_label or "start" in command_label:
            command_type = "create"
        elif "add" in command_label:
            command_type = "add"
        elif "complete" in command_label:
            command_type = "complete"
        elif "check" in command_label:
            command_type = "check"
        elif "delete" in command_label:
            command_type = "delete"
        else:
            command_type = command_label.split()[0]
            
        print(f"DEBUG - Input text: {input_text}")
        print(f"DEBUG - Command label: {command_label}")
        print(f"DEBUG - Command type: {command_type}")
        
        # Extract project name and requirements
        project_name = None
        requirements = []
        step = None
        
        # For project creation, look for technology keywords
        if command_type == "create":
            # Extract requirements
            tech_indicators = ["with", "using", "in"]
            for indicator in tech_indicators:
                if indicator in input_text.lower():
                    tech_part = input_text.split(indicator)[-1].strip()
                    requirements = [req.strip() for req in tech_part.split("and") if req.strip()]
                    break
            
            # Try to extract project type/name
            project_types = ["web development", "web", "mobile app", "mobile", "desktop app", "desktop", "backend", "frontend"]
            for proj_type in project_types:
                if proj_type in input_text.lower():
                    # For compound types like "web development", use the full phrase
                    if " " in proj_type:
                        project_name = f"{proj_type} project"
                    # For single word types, check if they're part of a compound phrase
                    else:
                        # Check if it's part of a compound phrase
                        words_before = 2  # Look for up to 2 words before
                        text_parts = input_text.lower().split()
                        for i, word in enumerate(text_parts):
                            if word == proj_type:
                                # Look backwards for compound phrase
                                start = max(0, i - words_before)
                                compound = " ".join(text_parts[start:i+1])
                                if compound in ["web development", "mobile app", "desktop app"]:
                                    project_name = f"{compound} project"
                                else:
                                    project_name = f"{proj_type} project"
                                break
                    break
            
            # If no specific type found, use a generic name
            if not project_name:
                project_name = "new project"
        
        # For adding steps, extract both project name and step
        elif command_type == "add":
            print("DEBUG - Processing add command")
            # First try to find project name from common patterns
            project_patterns = [
                r"in the (.*?)\s*project",
                r"to the (.*?)\s*project",
                r"to (.*?)\s*project",
                r"for the (.*?)\s*project",
                r"for (.*?)\s*project"
            ]
            
            for pattern in project_patterns:
                print(f"DEBUG - Trying pattern: {pattern}")
                match = re.search(pattern, input_text.lower())
                if match:
                    project_name = match.group(1).strip() + " project"
                    print(f"DEBUG - Found project name via pattern: {project_name}")
                    break
            
            # If no match found, look for project types
            if not project_name:
                print("DEBUG - No pattern match, trying project types")
                project_types = ["web development", "web", "mobile app", "mobile", "desktop app", "desktop", "backend", "frontend"]
                for proj_type in project_types:
                    print(f"DEBUG - Checking project type: {proj_type}")
                    if proj_type in input_text.lower():
                        print(f"DEBUG - Found project type: {proj_type}")
                        # For compound types like "web development", use the full phrase
                        if " " in proj_type:
                            project_name = f"{proj_type} project"
                        # For single word types, check if they're part of a compound phrase
                        else:
                            # Check if it's part of a compound phrase
                            words_before = 2  # Look for up to 2 words before
                            text_parts = input_text.lower().split()
                            for i, word in enumerate(text_parts):
                                if word == proj_type:
                                    # Look backwards for compound phrase
                                    start = max(0, i - words_before)
                                    compound = " ".join(text_parts[start:i+1])
                                    if compound in ["web development", "mobile app", "desktop app"]:
                                        project_name = f"{compound} project"
                                    else:
                                        project_name = f"{proj_type} project"
                                    break
                        break
            
            # Extract the step description
            step_indicators = ["implement", "add", "create", "build", "develop", "set up"]
            for indicator in step_indicators:
                if indicator in input_text.lower():
                    parts = input_text.lower().split(indicator, 1)
                    if len(parts) > 1:
                        step = indicator + parts[1].split("in the")[0].split("to the")[0].strip()
                        break
        
        # Rest of the existing code for other command types
        else:
            # Look for organization or product names as potential project names
            ner_results = ner_pipeline(input_text)
            project_entities = [ent for ent in ner_results if ent['entity'] in ['B-ORG', 'B-PRODUCT']]
            if project_entities:
                project_name = project_entities[0]['word']
        
        print(f"DEBUG - Project name: {project_name}")
        print(f"DEBUG - Step: {step}")
        print(f"DEBUG - Requirements: {requirements}")
        
        return command_type, project_name, requirements, step

    def parse_project_command(self, input_text: str) -> Tuple[str, Optional[str], Optional[List[str]], Optional[str]]:
        """Enhanced project command parsing using zero-shot classification"""
        # Define possible command types
        command_candidates = [
            "create new project",
            "start a new project",
            "start new project",
            "add step to project",
            "complete project",
            "check project status",
            "delete project"
        ]
        
        # Classify command type
        command_result = intent_classifier(input_text, command_candidates)
        command_label = command_result['labels'][0]
        print(f"DEBUG - All labels and scores:")
        for label, score in zip(command_result['labels'], command_result['scores']):
            print(f"  {label}: {score}")
        
        # Map command labels to command types
        if "create" in command_label or "start" in command_label:
            command_type = "create"
        elif "add" in command_label:
            command_type = "add"
        elif "complete" in command_label:
            command_type = "complete"
        elif "check" in command_label:
            command_type = "check"
        elif "delete" in command_label:
            command_type = "delete"
        else:
            command_type = command_label.split()[0]
            
        print(f"DEBUG - Input text: {input_text}")
        print(f"DEBUG - Command label: {command_label}")
        print(f"DEBUG - Command type: {command_type}")
        
        # Extract project name and requirements
        project_name = None
        requirements = []
        step = None
        
        # For project creation, look for technology keywords
        if command_type == "create":
            # Extract requirements
            tech_indicators = ["with", "using", "in"]
            for indicator in tech_indicators:
                if indicator in input_text.lower():
                    tech_part = input_text.split(indicator)[-1].strip()
                    requirements = [req.strip() for req in tech_part.split("and") if req.strip()]
                    break
            
            # Try to extract project type/name
            project_types = ["web development", "web", "mobile app", "mobile", "desktop app", "desktop", "backend", "frontend"]
            for proj_type in project_types:
                if proj_type in input_text.lower():
                    # For compound types like "web development", use the full phrase
                    if " " in proj_type:
                        project_name = f"{proj_type} project"
                    # For single word types, check if they're part of a compound phrase
                    else:
                        # Check if it's part of a compound phrase
                        words_before = 2  # Look for up to 2 words before
                        text_parts = input_text.lower().split()
                        for i, word in enumerate(text_parts):
                            if word == proj_type:
                                # Look backwards for compound phrase
                                start = max(0, i - words_before)
                                compound = " ".join(text_parts[start:i+1])
                                if compound in ["web development", "mobile app", "desktop app"]:
                                    project_name = f"{compound} project"
                                else:
                                    project_name = f"{proj_type} project"
                                break
                    break
            
            # If no specific type found, use a generic name
            if not project_name:
                project_name = "new project"
        
        # For adding steps, extract both project name and step
        elif command_type == "add":
            print("DEBUG - Processing add command")
            # First try to find project name from common patterns
            project_patterns = [
                r"in the (.*?)\s*project",
                r"to the (.*?)\s*project",
                r"to (.*?)\s*project",
                r"for the (.*?)\s*project",
                r"for (.*?)\s*project"
            ]
            
            for pattern in project_patterns:
                print(f"DEBUG - Trying pattern: {pattern}")
                match = re.search(pattern, input_text.lower())
                if match:
                    project_name = match.group(1).strip() + " project"
                    print(f"DEBUG - Found project name via pattern: {project_name}")
                    break
            
            # If no match found, look for project types
            if not project_name:
                print("DEBUG - No pattern match, trying project types")
                project_types = ["web development", "web", "mobile app", "mobile", "desktop app", "desktop", "backend", "frontend"]
                for proj_type in project_types:
                    print(f"DEBUG - Checking project type: {proj_type}")
                    if proj_type in input_text.lower():
                        print(f"DEBUG - Found project type: {proj_type}")
                        # For compound types like "web development", use the full phrase
                        if " " in proj_type:
                            project_name = f"{proj_type} project"
                        # For single word types, check if they're part of a compound phrase
                        else:
                            # Check if it's part of a compound phrase
                            words_before = 2  # Look for up to 2 words before
                            text_parts = input_text.lower().split()
                            for i, word in enumerate(text_parts):
                                if word == proj_type:
                                    # Look backwards for compound phrase
                                    start = max(0, i - words_before)
                                    compound = " ".join(text_parts[start:i+1])
                                    if compound in ["web development", "mobile app", "desktop app"]:
                                        project_name = f"{compound} project"
                                    else:
                                        project_name = f"{proj_type} project"
                                    break
                        break
            
            # Extract the step description
            step_indicators = ["implement", "add", "create", "build", "develop", "set up"]
            for indicator in step_indicators:
                if indicator in input_text.lower():
                    parts = input_text.lower().split(indicator, 1)
                    if len(parts) > 1:
                        step = indicator + parts[1].split("in the")[0].split("to the")[0].strip()
                        break
        
        # Rest of the existing code for other command types
        else:
            # Look for organization or product names as potential project names
            ner_results = ner_pipeline(input_text)
            project_entities = [ent for ent in ner_results if ent['entity'] in ['B-ORG', 'B-PRODUCT']]
            if project_entities:
                project_name = project_entities[0]['word']
        
        print(f"DEBUG - Project name: {project_name}")
        print(f"DEBUG - Step: {step}")
        print(f"DEBUG - Requirements: {requirements}")
        
        return command_type, project_name, requirements, step

# Initialize the engine
nlp_engine = NLPEngine()
