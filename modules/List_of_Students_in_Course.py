from Attendance.models import Course
from Attendance import app

with app.app_context():
    course = input("Please enter Course ID: ")

    course_id = Course.query.filter_by(Course_ID=course).first()

    x = course_id.Enrolled_Students_In_Course

    for i in x:
        print(i.Registration_No_Student)
