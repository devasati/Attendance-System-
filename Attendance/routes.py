from Attendance import app
from flask import render_template


# Main Entrance Page of website
@app.route('/')
@app.route('/VITrack')
def entrance_page():
    return render_template('m11_Entrance.html')


from Attendance import student_routes

from Attendance import faculty_routes
