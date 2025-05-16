from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, current_app
import calendar
from datetime import datetime
from bson import ObjectId
import traceback

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    today = datetime.now()
    cal = calendar.monthcalendar(today.year, today.month)
    
    # Get the daily fact
    daily_fact = current_app.ai_assistant.get_daily_fact()

    return render_template('index.html',
                           month=today.strftime("%B"),
                           year=today.year,
                           current_month=today.month,
                           current_year=today.year,
                           calendar=cal,
                           highlight_day=today.day,
                           daily_fact=daily_fact)

@main_bp.route('/calendar/<int:year>/<int:month>')
def calendar_view(year, month):
    db = current_app.db
    events = db['events']

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # Handle month wrapping
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    today = datetime.now()

    user_events = list(events.find({
        'user_id': session['user_id'],
        'date': {'$regex': f'^{year}-{month:02d}'}
    }))

    return render_template('index.html', calendar=cal, month=month_name, year=year,
                           current_month=month, current_year=year,
                           highlight_day=today.day if month == today.month and year == today.year else None,
                           events=user_events)

@main_bp.route('/save_event', methods=['POST'])
def save_event():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not logged in'}), 401

        db = current_app.db
        events = db['events']
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        print(f"Received event data: {data}")  # Debug log

        # Validate and parse the date
        try:
            event_date = datetime.strptime(data.get('date'), '%Y-%m-%d')
            data['date'] = event_date.strftime('%Y-%m-%d')  # reformat to standard
        except (ValueError, TypeError) as e:
            print(f"Date parsing error: {str(e)}")  # Debug log
            return jsonify({'error': 'Invalid date format. Expected YYYY-MM-DD.'}), 400

        # Add user and creation info
        data.update({
            'user_id': session['user_id'],
            'created_at': datetime.now()
        })

        print(f"Final event data to save: {data}")  # Debug log

        try:
            if '_id' in data:
                # Update existing event
                print(f"Updating event with ID: {data['_id']}")  # Debug log
                try:
                    object_id = ObjectId(data['_id'])
                except Exception as e:
                    print(f"Invalid ObjectId format: {str(e)}")  # Debug log
                    return jsonify({'error': 'Invalid event ID format'}), 400

                # Remove _id from update data to prevent immutable field error
                update_data = {k: v for k, v in data.items() if k != '_id'}
                print(f"Update data (without _id): {update_data}")  # Debug log

                result = events.update_one(
                    {'_id': object_id, 'user_id': session['user_id']},
                    {'$set': update_data}
                )
                print(f"Update result: {result.raw_result}")  # Debug log
                
                if result.modified_count == 0:
                    # Check if the event exists
                    existing_event = events.find_one({'_id': object_id})
                    if not existing_event:
                        return jsonify({'error': 'Event not found'}), 404
                    elif existing_event['user_id'] != session['user_id']:
                        return jsonify({'error': 'Unauthorized to modify this event'}), 403
                    else:
                        return jsonify({'error': 'No changes made to the event'}), 400
                return jsonify({'success': True})
            else:
                # Create new event
                print("Creating new event")  # Debug log
                result = events.insert_one(data)
                print(f"Insert result: {result.raw_result}")  # Debug log
                return jsonify({'success': True, 'event_id': str(result.inserted_id)})
        except Exception as e:
            print(f"Database error details: {str(e)}")  # Debug log
            print(f"Database error traceback: {traceback.format_exc()}")  # Debug log
            return jsonify({'error': f'Database error: {str(e)}'}), 500

    except Exception as e:
        print(f"Error in save_event: {str(e)}")  # Debug log
        print(f"Error traceback: {traceback.format_exc()}")  # Debug log
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@main_bp.route('/delete_event', methods=['POST'])
def delete_event():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not logged in'}), 401

        data = request.get_json()
        if not data or 'event_id' not in data:
            return jsonify({'error': 'No event ID provided'}), 400

        db = current_app.db
        events = db['events']
        
        result = events.delete_one({
            '_id': ObjectId(data['event_id']),
            'user_id': session['user_id']
        })
        
        if result.deleted_count:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Event not found'}), 404
    except Exception as e:
        print(f"Error in delete_event: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': 'An error occurred while deleting the event'}), 500

@main_bp.route('/get_events', methods=['GET'])
def get_events():
    db = current_app.db
    events = db['events']
    year, month = int(request.args['year']), int(request.args['month'])
    event_list = list(events.find({
        'user_id': session['user_id'],
        'date': {'$regex': f'^{year}-{month:02d}'}
    }).sort([
        ('date', 1),  # Sort by date ascending
        ('time', 1)   # Then by time ascending
    ]))
    for e in event_list:
        e['_id'] = str(e['_id'])
    return jsonify(event_list)

@main_bp.route('/chat_with_ai', methods=['POST'])
def chat_with_ai():
    try:
        if 'user_id' not in session:
            print("User not logged in")  # Debug log
            return jsonify({'error': 'Not logged in'}), 401

        assistant = current_app.ai_assistant
        data = request.get_json()
        if not data or 'message' not in data:
            print("No message provided in request")  # Debug log
            return jsonify({'error': 'No message provided'}), 400

        user_message = data['message']
        print(f"Processing message from user {session['user_id']}: {user_message}")  # Debug log
        
        response = assistant.process_calendar_request(user_message, session['user_id'])
        print(f"AI Assistant response: {response}")  # Debug log
        
        # Ensure response is a dictionary
        if not isinstance(response, dict):
            print(f"Invalid response type: {type(response)}")  # Debug log
            return jsonify({
                'error': 'Invalid response format from AI assistant',
                'output_llm': 'I apologize, but I encountered an error processing your request. Please try again.'
            }), 500
            
        # Check if response contains an error
        if 'error' in response:
            print(f"Error in response: {response['error']}")  # Debug log
            return jsonify(response), 500
            
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in chat_with_ai: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': 'An error occurred while processing your request',
            'output_llm': 'I apologize, but I encountered an error processing your request. Please try again.'
        }), 500

@main_bp.route('/process_pending_event', methods=['POST'])
def process_pending_event():
    assistant = current_app.ai_assistant
    event_id = request.get_json().get('event_id')
    assistant.mark_event_processed(event_id)
    return jsonify({'success': True})

@main_bp.route('/get_daily_fact')
def get_daily_fact():
    """Endpoint to get the daily fact"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    fact = current_app.ai_assistant.get_daily_fact()
    return jsonify({'fact': fact})

@main_bp.route('/get_chat_history')
def get_chat_history():
    """Get the last 3 messages from chat history"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        # Get last 3 interactions from llm_info
        recent_interactions = list(current_app.db['llm_info'].find(
            {'user_id': session['user_id']},
            sort=[('created_at', -1)],
            limit=3
        ))
        
        # Convert to chat history format
        history = []
        for interaction in reversed(recent_interactions):  # Reverse to get chronological order
            if 'user_message' in interaction:
                history.append({
                    "role": "user",
                    "content": interaction['user_message']
                })
            if 'output_llm' in interaction:
                history.append({
                    "role": "assistant",
                    "content": interaction['output_llm']
                })
        
        return jsonify({'history': history})
    except Exception as e:
        print(f"Error getting chat history: {str(e)}")
        return jsonify({'error': 'Error getting chat history'}), 500
