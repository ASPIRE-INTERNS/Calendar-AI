import requests
import json
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

class OllamaAssistant:
    def __init__(self, model_name=None):
        self.model_name = model_name or os.getenv("OLLAMA_MODEL_NAME", "llama3.2")
        self.base_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
        
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client['calendar']
        self.llm_info = self.db['llm_info']
        self.events = self.db['events']
        
    def generate_response(self, prompt):
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(self.base_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "I'm sorry, I couldn't generate a response.")
            
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Ollama: {e}")
            return "I'm sorry, I'm having trouble connecting to the AI service right now."
            
    def process_calendar_request(self, user_message, user_id):
        # Add context about calendar functionality
        context = """
        You are an AI assistant for a calendar application. You can help users with:
        - Creating events
        - Managing reminders
        - Scheduling tasks
        - Answering questions about their calendar
        - Providing calendar-related suggestions
        
        When creating an event, reminder, or task, please extract the following information:
        - Title
        - Description (if provided)
        - Date (in YYYY-MM-DD format)
        - Time (in HH:MM format)
        - Type (Event, Reminder, or Task)
        - Recurrence (none, daily, weekly, monthly, yearly)
        
        For dates:
        - Use today's date if the user says "today"
        - Use tomorrow's date if the user says "tomorrow"
        - Use the actual date if provided
        - Always use YYYY-MM-DD format
        
        Please provide your response in JSON format with the following structure:
        {
            "output_llm": "Your response message here",
            "event_data": {
                "type": "task/event/reminder",
                "title": "...",
                "description": "...",
                "date": "YYYY-MM-DD",
                "time": "HH:MM",
                "recurrence": "none"
            }
        }
        
        If you're creating an event, your output_llm should be a confirmation message like:
        "I've created your [type]: [title] on [date] at [time]"
        
        If you're not creating an event, set event_data to null and provide a helpful response in output_llm.
        """
        
        full_prompt = f"{context}\n\nUser: {user_message}\nAssistant:"
        response = self.generate_response(full_prompt)
        
        try:
            # Parse the JSON response
            response_data = json.loads(response)
            
            # Save the interaction to llm_info collection
            self.llm_info.insert_one({
                'user_id': user_id,
                'user_message': user_message,
                'output_llm': response_data.get('output_llm', ''),
                'created_at': datetime.now()
            })
            
            # If there's event data, save it to events collection
            event_data = response_data.get('event_data')
            if event_data:
                # Ensure the date is in the correct format
                try:
                    # Parse the date to validate it
                    datetime.strptime(event_data['date'], '%Y-%m-%d')
                except ValueError:
                    # If date is invalid, use today's date
                    event_data['date'] = datetime.now().strftime('%Y-%m-%d')
                
                event_data['user_id'] = user_id
                event_data['created_at'] = datetime.now()
                self.events.insert_one(event_data)
                
            return response_data
            
        except json.JSONDecodeError:
            # If the response isn't valid JSON, save it as a regular message
            self.llm_info.insert_one({
                'user_id': user_id,
                'user_message': user_message,
                'output_llm': response,
                'created_at': datetime.now()
            })
            return {
                'output_llm': response,
                'event_data': None
            }
        
    def get_pending_events(self, user_id):
        """Get all pending events from llm_info that haven't been processed yet"""
        return list(self.llm_info.find({
            'user_id': user_id,
            'processed': False
        }))
        
    def mark_event_processed(self, event_id):
        """Mark an event as processed in llm_info"""
        self.llm_info.update_one(
            {'_id': ObjectId(event_id)},
            {'$set': {'processed': True}}
        ) 