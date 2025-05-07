from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, current_app
import calendar
from datetime import datetime
from bson import ObjectId

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    today = datetime.now()
    cal = calendar.monthcalendar(today.year, today.month)

    return render_template('index.html',
                           month=today.strftime("%B"),
                           year=today.year,
                           current_month=today.month,
                           current_year=today.year,
                           calendar=cal,
                           highlight_day=today.day)

@main_bp.route('/calendar/<int:year>/<int:month>')
def calendar_view(year, month):
    db = current_app.db
    events = db['events']

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

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
    if '_id' in data:
        result = events.update_one(
            {'_id': ObjectId(data['_id']), 'user_id': session['user_id']},
            {'$set': data}
        )
        return jsonify({'success': True}) if result.modified_count else jsonify({'error': 'Not found'}), 404
    else:
        data.update({'user_id': session['user_id'], 'created_at': datetime.now()})
        event_id = events.insert_one(data).inserted_id
        return jsonify({'success': True, 'event_id': str(event_id)})

@main_bp.route('/delete_event', methods=['POST'])
def delete_event():
    db = current_app.db
    events = db['events']
    data = request.get_json()
    result = events.delete_one({'_id': ObjectId(data['event_id']), 'user_id': session['user_id']})
    return jsonify({'success': True}) if result.deleted_count else jsonify({'error': 'Not found'}), 404

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
    assistant = current_app.ai_assistant
    user_message = request.get_json().get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    response = assistant.process_calendar_request(user_message, session['user_id'])
    return jsonify(response)

@main_bp.route('/process_pending_event', methods=['POST'])
def process_pending_event():
    assistant = current_app.ai_assistant
    event_id = request.get_json().get('event_id')
    assistant.mark_event_processed(event_id)
    return jsonify({'success': True})
