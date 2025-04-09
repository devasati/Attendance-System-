from Attendance import app
from Attendance.models import Course

with app.app_context():

    course = int(input("Please Enter the Course ID:"))
    x = Course.query.filter_by(Course_ID=course).first()
    y = x.Course_Lectures
    if y:
        print("Available Lectures:")
        for lecture in y:
            print(lecture.Lecture_ID)
    else:
        print("No Lectures Available.")
