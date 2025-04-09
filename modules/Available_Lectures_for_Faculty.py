from Attendance import app
from Attendance.models import UserFaculty

with app.app_context():
    faculty = input("Please Enter the Faculty Number:")
    x = UserFaculty.query.filter_by(Employee_No_Faculty=faculty).first()
    y = x.Faculty_Lectures
    if y:
        print("Available Lectures:")
        for lecture in y:
            print(lecture.Lecture_ID)
    else:
        print("No Lectures Available.")
