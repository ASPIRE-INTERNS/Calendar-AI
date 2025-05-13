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
    db = current_app.db
    events = db['events']

    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json()

    # Validate and parse the date
    try:
        event_date = datetime.strptime(data.get('date'), '%Y-%m-%d')
        data['date'] = event_date.strftime('%Y-%m-%d')  # reformat to standard
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date format. Expected YYYY-MM-DD.'}), 400

    data.update({'user_id': session['user_id'], 'created_at': datetime.now()})

    if '_id' in data:
        result = events.update_one(
            {'_id': ObjectId(data['_id']), 'user_id': session['user_id']},
            {'$set': data}
        )
        return jsonify({'success': True}) if result.modified_count else jsonify({'error': 'Not found'}), 404
    else:
        event_id = events.insert_one(data).inserted_id
        return jsonify({'success': True, 'event_id': str(event_id)})

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
    }))
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
