from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    db = current_app.db
    users = db['users']

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    db = current_app.db
    users = db['users']

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users.find_one({'username': username}):
            flash('Username already exists.', 'danger')
            return redirect(url_for('auth.signup'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        user_id = users.insert_one({
            'username': username,
            'password': hashed_password,
            'created_at': datetime.now()
        }).inserted_id

        session['user_id'] = str(user_id)
        session['username'] = username
        flash('Account created successfully!', 'success')
        return redirect(url_for('main.home'))
    return render_template('signup.html')

@auth_bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    db = current_app.db
    users = db['users']

    if request.method == 'POST':
        username = request.form.get('username')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        user = users.find_one({'username': username})
        if not user or not check_password_hash(user['password'], current_password):
            flash('Incorrect current password or user not found.', 'danger')
            return redirect(url_for('auth.change_password'))

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.change_password'))

        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        users.update_one({'username': username}, {'$set': {'password': hashed_password}})
        flash('Password updated successfully!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('change_password.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'success')
    return redirect(url_for('auth.login'))
