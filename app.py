import re
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
import calendar
from datetime import datetime
import secrets
from pymongo import MongoClient
from bson import ObjectId
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from ai_assistant import OllamaAssistant

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'secrets.token_hex(16)'  # Secret key for session management

# Initialize AI assistant
ai_assistant = OllamaAssistant()

# MongoDB connection
try:
    client = MongoClient('mongodb://localhost:27017/calendar')
    db = client['calendar']  # This creates/uses the database named 'calendar'
    users_collection = db['users']
    events_collection = db['events']
    logger.info("Successfully connected to MongoDB")
    logger.info(f"Database: {db.name}")
    logger.info(f"Collections: {db.list_collection_names()}")
except Exception as e:
    logger.error(f"Error connecting to MongoDB: {e}")
    raise


@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get current date
    today = datetime.now()
    month = today.strftime("%B")
    year = today.year
    current_month = today.month
    current_year = today.year
    
    # Generate calendar for current month
    cal = calendar.monthcalendar(year, current_month)
    highlight_day = today.day if today.month == current_month and today.year == current_year else None
    
    return render_template('index.html', 
                         month=month,
                         year=year,
                         current_month=current_month,
                         current_year=current_year,
                         calendar=cal,
                         highlight_day=highlight_day)

@app.route('/calendar/<int:year>/<int:month>')
def calendar_view(year, month):
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Ensure user is logged in

    # Ensure month is within valid range
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    today = datetime.now()
    highlight_day = today.day if today.month == month and today.year == year else None

    # Get user's events for the current month
    user_events = list(events_collection.find({
        'user_id': session['user_id'],
        'date': {
            '$regex': f'^{year}-{month:02d}'
        }
    }))

    return render_template('index.html', 
                           calendar=cal, 
                           month=month_name, 
                           year=year, 
                           current_month=month, 
                           current_year=year,
                           highlight_day=highlight_day,
                           events=user_events)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username exists
        user = users_collection.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if username already exists
        if users_collection.find_one({'username': username}):
            flash('Username already exists. Please choose another.', 'danger')
            return redirect(url_for('signup'))
        
        # Hash the password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Create new user
        user_id = users_collection.insert_one({
            'username': username,
            'password': hashed_password,
            'created_at': datetime.now()
        }).inserted_id
        
        session['user_id'] = str(user_id)
        session['username'] = username
        flash('Account created successfully!', 'success')
        return redirect(url_for('home'))
    
    return render_template('signup.html')

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        username = request.form.get('username')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Get user from database
        user = users_collection.find_one({'username': username})
        
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('change_password'))
            
        # If user is logged in, verify current password
        if 'username' in session and session['username'] == username:
            if not check_password_hash(user['password'], current_password):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('change_password'))
        else:
            # If not logged in, require current password
            if not current_password or not check_password_hash(user['password'], current_password):
                flash('Current password is required and must be correct', 'danger')
                return redirect(url_for('change_password'))
            
        # Check if new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('change_password'))
            
        # Update password
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        users_collection.update_one(
            {'username': username},
            {'$set': {'password': hashed_password}}
        )
        
        flash('Password changed successfully', 'success')
        return redirect(url_for('login'))
        
    return render_template('change_password.html')

@app.route('/save_event', methods=['POST'])
def save_event():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        data = request.get_json()
        logger.debug(f"Received event data: {data}")
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['title', 'date', 'time', 'type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        event_data = {
            'user_id': session['user_id'],
            'title': data['title'],
            'description': data.get('description', ''),
            'date': data['date'],
            'time': data['time'],
            'recurrence': data.get('recurrence', 'none'),
            'type': data['type'],
            'created_at': datetime.now()
        }

        logger.debug(f"Prepared event data: {event_data}")

        # If editing an existing event
        if '_id' in data:
            logger.debug(f"Updating event with ID: {data['_id']}")
            result = events_collection.update_one(
                {'_id': ObjectId(data['_id']), 'user_id': session['user_id']},
                {'$set': event_data}
            )
            logger.debug(f"Update result: {result.modified_count} documents modified")
            if result.modified_count == 0:
                return jsonify({'error': 'Event not found or not authorized'}), 404
            return jsonify({'success': True, 'event_id': data['_id']})
        else:
            # Create new event
            logger.debug("Creating new event")
            result = events_collection.insert_one(event_data)
            logger.debug(f"Insert result: {result.inserted_id}")
            return jsonify({'success': True, 'event_id': str(result.inserted_id)})

    except Exception as e:
        logger.error(f"Error in save_event: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete_event', methods=['POST'])
def delete_event():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.json
    result = events_collection.delete_one({
        '_id': ObjectId(data['event_id']),
        'user_id': session['user_id']
    })

    if result.deleted_count > 0:
        return jsonify({'success': True})
    return jsonify({'error': 'Event not found'}), 404

@app.route('/get_events', methods=['GET'])
def get_events():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        year = int(request.args.get('year'))
        month = int(request.args.get('month'))
        
        logger.debug(f"Fetching events for user {session['user_id']}, year: {year}, month: {month}")
        
        # Count total events in collection
        total_events = events_collection.count_documents({})
        logger.debug(f"Total events in collection: {total_events}")
        
        # Count user's events
        user_events_count = events_collection.count_documents({'user_id': session['user_id']})
        logger.debug(f"User's events count: {user_events_count}")

        events = list(events_collection.find({
            'user_id': session['user_id'],
            'date': {
                '$regex': f'^{year}-{month:02d}'
            }
        }))

        logger.debug(f"Found {len(events)} events for the specified month")

        # Convert ObjectId to string for JSON serialization
        for event in events:
            event['_id'] = str(event['_id'])

        return jsonify(events)
    except Exception as e:
        logger.error(f"Error in get_events: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/chat_with_ai', methods=['POST'])
def chat_with_ai():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
            
        # Get AI response
        response_data = ai_assistant.process_calendar_request(user_message, session['user_id'])
        
        return jsonify({
            'success': True,
            'output_llm': response_data.get('output_llm', ''),
            'event_data': response_data.get('event_data')
        })
        
    except Exception as e:
        logger.error(f"Error in chat_with_ai: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/process_pending_event', methods=['POST'])
def process_pending_event():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        data = request.get_json()
        event_id = data.get('event_id')
        
        if not event_id:
            return jsonify({'error': 'No event ID provided'}), 400
            
        # Mark the event as processed
        ai_assistant.mark_event_processed(event_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error in process_pending_event: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
