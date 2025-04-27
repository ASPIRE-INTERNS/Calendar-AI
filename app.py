from flask import Flask, render_template, request, redirect, url_for
import calendar
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    now = datetime.now()
    return redirect(url_for('calendar_view', year=now.year, month=now.month))

@app.route('/calendar/<int:year>/<int:month>')
def calendar_view(year, month):
    # Handling overflows
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    today = datetime.now()
    # Only highlight if we are on the current month and year
    highlight_day = today.day if today.month == month and today.year == year else None

    return render_template('index.html', 
                           calendar=cal, 
                           month=month_name, 
                           year=year, 
                           current_month=month, 
                           current_year=year,
                           highlight_day=highlight_day)

if __name__ == "__main__":
    app.run(debug=True)

