import requests
import json
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId
from flask import current_app
from app.utils.enums import EventType
import traceback

class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class OllamaAssistant:
    def __init__(self, model_name=None, base_url=None, mongo_uri=None):
        self.model_name = model_name
        self.base_url = base_url
        self.client = MongoClient(mongo_uri) if mongo_uri else None
        self.db = None
        self.llm_info = None
        self.events = None
        self.daily_facts = None
        self.json_encoder = MongoJSONEncoder()
        self.conversation_history = []

    def init_app(self, app):
        """Initialize the assistant with app configuration"""
        self.model_name = self.model_name or app.config['OLLAMA_MODEL_NAME']
        self.base_url = self.base_url or app.config['OLLAMA_API_URL']
        self.client = self.client or MongoClient(app.config['MONGO_URI'])
        self.db = self.client['calendar']
        self.llm_info = self.db['llm_info']
        self.events = self.db['events']
        self.daily_facts = self.db['daily_facts']

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
            
    def get_conversation_context(self, user_message, user_id):
        """Get the last 3 messages for context from llm_info"""
        # Get last 3 interactions from llm_info
        recent_interactions = list(self.llm_info.find(
            {'user_id': user_id},
            sort=[('created_at', -1)],
            limit=3
        ))
        
        # Convert to conversation history format
        self.conversation_history = []
        for interaction in reversed(recent_interactions):  # Reverse to get chronological order
            if 'user_message' in interaction:
                self.conversation_history.append({
                    "role": "user",
                    "content": interaction['user_message']
                })
            if 'output_llm' in interaction:
                self.conversation_history.append({
                    "role": "assistant",
                    "content": interaction['output_llm']
                })
        
        # Add the new message
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Keep only the last 3 messages
        if len(self.conversation_history) > 3:
            self.conversation_history = self.conversation_history[-3:]
        
        # Format the conversation history
        context = "Previous conversation:\n"
        for msg in self.conversation_history:
            role = "User" if msg["role"] == "user" else "Assistant"
            context += f"{role}: {msg['content']}\n"
        
        return context
            
    def process_calendar_request(self, user_message, user_id):
        try:
            print(f"Processing calendar request for user {user_id}: {user_message}")  # Debug log
            # Get current date and time
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M")
            current_day = now.strftime("%A")
            tomorrow_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Format current date for display
            current_date_display = now.strftime("%A, %B %d")
            
            # Calculate next month's first day
            if now.month == 12:
                next_month_date = datetime(now.year + 1, 1, 1)
            else:
                next_month_date = datetime(now.year, now.month + 1, 1)
            next_month_first = next_month_date.strftime("%Y-%m-%d")
            
            # Calculate next month's second day
            next_month_second = (next_month_date + timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Calculate next month's first occurrence of each day of the week
            next_month_weekdays = {}
            for i in range(7):  # 0 = Monday, 6 = Sunday
                # Find the first occurrence of this weekday in next month
                days_until = (i - next_month_date.weekday()) % 7
                first_occurrence = next_month_date + timedelta(days=days_until)
                day_name = first_occurrence.strftime("%A").lower()
                next_month_weekdays[day_name] = first_occurrence.strftime("%Y-%m-%d")
            
            # Calculate next week's dates for all days
            next_week_dates = {}
            for i in range(7):  # 0 = Monday, 6 = Sunday
                days_until = (i - now.weekday()) % 7
                if days_until == 0:  # If it's today, get next week's date
                    days_until = 7
                next_date = now + timedelta(days=days_until)
                day_name = next_date.strftime("%A")
                next_week_dates[day_name.lower()] = next_date.strftime("%Y-%m-%d")
            
            # Get conversation history from MongoDB
            conversation_context = self.get_conversation_context(user_message, user_id)
            
            # Add context about calendar functionality
            context = f"""
                    {conversation_context}

                    Current Date and Time Information:
                    - Today's date: {current_date}
                    - Current date display: {current_date_display}
                    - Current time: {current_time}
                    - Current day: {current_day}
                    - Tomorrow's date: {tomorrow_date}
                    - Next month's first day: {next_month_first}
                    - Next month's second day: {next_month_second}
                    - Next month's first Monday: {next_month_weekdays['monday']}
                    - Next month's first Tuesday: {next_month_weekdays['tuesday']}
                    - Next month's first Wednesday: {next_month_weekdays['wednesday']}
                    - Next month's first Thursday: {next_month_weekdays['thursday']}
                    - Next month's first Friday: {next_month_weekdays['friday']}
                    - Next month's first Saturday: {next_month_weekdays['saturday']}
                    - Next month's first Sunday: {next_month_weekdays['sunday']}
                    - Next Monday: {next_week_dates['monday']}
                    - Next Tuesday: {next_week_dates['tuesday']}
                    - Next Wednesday: {next_week_dates['wednesday']}
                    - Next Thursday: {next_week_dates['thursday']}
                    - Next Friday: {next_week_dates['friday']}
                    - Next Saturday: {next_week_dates['saturday']}
                    - Next Sunday: {next_week_dates['sunday']}

                    You are an AI assistant for a calendar application. You can help users with:
                    - Creating events
                    - Managing reminders
                    - Scheduling tasks
                    - Showing existing events/reminders/tasks for a specific date, week, or month
                    - Answering questions about their calendar
                    - Providing calendar-related suggestions

                    IMPORTANT: You MUST respond in valid JSON format with the following structure:
                    {{
                        "output_llm": "Your response message here",
                        "event_data": {{
                            "title": "...",
                            "description": "...",
                            "date": "YYYY-MM-DD",
                            "time": "HH:MM",
                            "recurrence": "none",
                            "type": "{', '.join([t.value for t in EventType])}"
                        }}
                    }}

                    Time Handling Rules:
                    1. For 24-hour format:
                       - Use "HH:MM" format (e.g., "23:00" for 11 PM)
                       - Single digits should be padded with leading zeros
                       - Valid hours are 00-23
                       - Valid minutes are 00-59
                    
                    2. For 12-hour format:
                       - Convert to 24-hour format internally
                       - "11 AM" becomes "11:00"
                       - "11 PM" becomes "23:00"
                       - "12 AM" becomes "00:00"
                       - "12 PM" becomes "12:00"
                    
                    3. For single numbers:
                       - If number is 1-12, assume AM
                       - If number is 13-23, use as is
                       - Always add ":00" for minutes
                       - Examples:
                         * "11" becomes "11:00"
                         * "23" becomes "23:00"
                         * "1" becomes "01:00"
                    
                    4. For unclear times:
                       - Ask for clarification
                       - Suggest common times (e.g., "Would you like 11:00 AM or 11:00 PM?")
                       - Set event_data to null until clarified

                    Title Guidelines:
                    1. For reminders:
                       - Use the main purpose as the title
                       - Don't include time in the title
                       - Make it descriptive and specific
                       - Examples:
                         * "Bathing" for a bathing reminder
                         * "Take Medication" for a medication reminder
                         * "Water Plants" for a plant watering reminder
                    
                    2. For tasks:
                       - Include the action and object
                       - Make it actionable
                       - Examples:
                         * "Complete Project Report"
                         * "Submit Assignment"
                         * "Buy Groceries"
                    
                    3. For events:
                       - Include the event type and purpose
                       - Add context if needed
                       - Examples:
                         * "Team Meeting: Project Review"
                         * "Doctor Appointment"
                         * "Birthday Party"

                    Example responses:
                    1. Creating a reminder:
                    {{
                        "output_llm": "I've scheduled your Reminder: 'Bathing' for {current_date_display} at 11:00 AM. You can view it in your calendar.",
                        "event_data": {{
                            "title": "Bathing",
                            "description": "Daily bathing reminder",
                            "date": "{current_date}",
                            "time": "11:00",
                            "recurrence": "none",
                            "type": "reminder"
                        }}
                    }}

                    2. Unclear time:
                    {{
                        "output_llm": "I need to clarify the time. Would you like to schedule this for 11:00 AM or 11:00 PM?",
                        "event_data": null
                    }}

                    3. General greeting:
                    {{
                        "output_llm": "Hello! How can I help you with your calendar today?",
                        "event_data": null
                    }}
                    """

            
            full_prompt = f"{context}\n\nUser: {user_message}\nAssistant:"
            print(f"Sending prompt to AI: {full_prompt}")  # Debug log
            response = self.generate_response(full_prompt)
            print(f"Raw AI response: {response}")  # Debug log
            
            try:
                # Parse the JSON response
                response_data = json.loads(response)
                print(f"Parsed response data: {response_data}")  # Debug log
                
                # Validate response structure
                if not isinstance(response_data, dict):
                    return {
                        "output_llm": "I'm sorry, I had trouble processing your request. Please try again.",
                        "event_data": None
                    }
                
                # Ensure required fields exist
                if 'output_llm' not in response_data:
                    response_data['output_llm'] = "I'm sorry, I had trouble processing your request. Please try again."
                
                # Add the assistant's response to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response_data.get('output_llm', '')
                })
                
                # Save the interaction to llm_info collection
                interaction_id = self.llm_info.insert_one({
                    'user_id': user_id,
                    'user_message': user_message,
                    'output_llm': response_data.get('output_llm', ''),
                    'created_at': datetime.now(),
                    'processed': False
                }).inserted_id 
                
                # If there's event data, save it to events collection
                event_data = response_data.get('event_data')
                if event_data:
                    try:
                        print(f"Processing event data: {event_data}")  # Debug log
                        
                        # Validate event type
                        event_type = event_data.get('type', '').lower()
                        if event_type not in [t.value for t in EventType]:
                            print(f"Invalid event type: {event_type}, defaulting to event")  # Debug log
                            event_data['type'] = EventType.EVENT.value  # Default to event if invalid type
                        
                        # Ensure the date is in the correct format
                        try:
                            # Parse the date to validate it
                            event_date = datetime.strptime(event_data['date'], '%Y-%m-%d')
                            print(f"Parsed event date: {event_date}")  # Debug log
                            
                            # If the date is today but the time has passed, move it to tomorrow
                            if event_date.date() == now.date():
                                event_time = datetime.strptime(event_data['time'], '%H:%M').time()
                                if event_time < now.time():
                                    print(f"Moving event to tomorrow as time has passed")  # Debug log
                                    event_data['date'] = tomorrow_date
                            
                            # Ensure the date is not in the past
                            if event_date.date() < now.date():
                                print(f"Date is in the past, using today's date")  # Debug log
                                event_data['date'] = current_date
                            
                            # Format the date for display
                            date_obj = datetime.strptime(event_data['date'], '%Y-%m-%d')
                            date_display = date_obj.strftime('%A, %B %d')
                            time_display = datetime.strptime(event_data['time'], '%H:%M').strftime('%I:%M %p')
                            title_display = event_data['title']
                            event_type_display = event_data['type'].capitalize()
                            
                            # Update the response message with the correct date format
                            response_data['output_llm'] = f"I've scheduled your {event_type_display}: '{title_display}' for {date_display} at {time_display}. You can view it in your calendar."
                            
                        except ValueError as e:
                            print(f"Date parsing error: {e}")
                            print(f"Invalid date format: {event_data.get('date')}")  # Debug log
                            # If date is invalid, use today's date
                            event_data['date'] = current_date
                        
                        # Ensure all required fields are present
                        if not event_data.get('title'):
                            event_data['title'] = 'Untitled Event'
                        if not event_data.get('description'):
                            event_data['description'] = ''
                        if not event_data.get('recurrence'):
                            event_data['recurrence'] = 'none'
                        
                        # Add user and creation info
                        event_data['user_id'] = user_id
                        event_data['created_at'] = datetime.now()
                        
                        print(f"Final event data before saving: {event_data}")  # Debug log
                        
                        # Save the event
                        event_id = self.events.insert_one(event_data).inserted_id
                        print(f"Event saved with ID: {event_id}")  # Debug log
                        
                        # Update the interaction with the event ID
                        self.llm_info.update_one(
                            {'_id': interaction_id},
                            {'$set': {
                                'event_id': event_id,
                                'processed': True
                            }}
                        )
                        
                        # Get the saved event for response
                        saved_event = self.events.find_one({'_id': event_id})
                        if saved_event:
                            # Convert ObjectId to string for JSON serialization
                            saved_event['_id'] = str(saved_event['_id'])
                            saved_event['user_id'] = str(saved_event['user_id'])
                            response_data['event_data'] = saved_event
                        
                    except Exception as e:
                        print(f"Error creating event: {e}")
                        print(f"Event data that caused error: {event_data}")  # Debug log
                        return {
                            "output_llm": "I'm sorry, I encountered an error while creating your event. Please try again.",
                            "event_data": None
                        }

                return response_data
                
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Invalid JSON response: {response}")  # Debug log
                # Try to extract a meaningful response from the raw text
                if isinstance(response, str) and len(response.strip()) > 0:
                    return {
                        "output_llm": response.strip(),
                        "event_data": None
                    }
                return {
                    "output_llm": "I'm sorry, I had trouble processing your request. Please try again.",
                    "event_data": None
                }
                
        except Exception as e:
            print(f"Error in process_calendar_request: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")  # Debug log
            return {
                "output_llm": "I'm sorry, an error occurred while processing your request.",
                "event_data": None
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

    def generate_daily_fact(self):
        """Generate a new daily fact using the LLM"""
        today = datetime.now()
        date_str = today.strftime('%B %d')  # e.g., "May 09"
        
        prompt = f"""Today is {date_str}. Generate an interesting, educational, and engaging "Did You Know?" fact specifically related to today's date (month and day) in history or science.
        The fact should be:
        - True and verifiable
        - Educational and informative
        - Engaging and surprising
        - Appropriate for all ages
        - Related to science, history, technology, or general knowledge
        
        Format the response as a JSON object with a single field 'fact' containing the fact text.
        Keep the fact concise (1-2 sentences).
        Example response format: {{"fact": "Did you know that on {date_str}, [interesting fact]?"}}"""

        try:
            response = self.generate_response(prompt)
            
            # Check if the response indicates LLM service is unavailable
            if response == "I'm sorry, I'm having trouble connecting to the AI service right now.":
                return response
                
            try:
                fact_data = json.loads(response)
                fact_text = fact_data.get('fact', '')
                
                if not fact_text:
                    # Fallback fact if the response is empty
                    fact_text = f"Did you know that on {date_str}, many significant events in history have occurred? Today is a great day to learn something new!"
                
                # Store the fact with today's date
                self.daily_facts.update_one(
                    {'date': today.strftime('%Y-%m-%d')},
                    {'$set': {
                        'fact': fact_text,
                        'date': today.strftime('%Y-%m-%d'),
                        'created_at': datetime.now()
                    }},
                    upsert=True
                )
                return fact_text
            except json.JSONDecodeError:
                # If JSON parsing fails, use the raw response as the fact
                fact_text = response if response else f"Did you know that on {date_str}, many significant events in history have occurred? Today is a great day to learn something new!"
                self.daily_facts.update_one(
                    {'date': today.strftime('%Y-%m-%d')},
                    {'$set': {
                        'fact': fact_text,
                        'date': today.strftime('%Y-%m-%d'),
                        'created_at': datetime.now()
                    }},
                    upsert=True
                )
                return fact_text
        except Exception as e:
            print(f"Error generating daily fact: {e}")
            return "I'm sorry, I'm having trouble connecting to the AI service right now."

    def get_daily_fact(self):
        """Get today's fact or generate a new one if none exists"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Try to get today's fact
        fact_doc = self.daily_facts.find_one({'date': today})
        
        if fact_doc:
            return fact_doc['fact']
        
        # If no fact exists for today, generate a new one
        return self.generate_daily_fact() 
        return self.generate_daily_fact() 