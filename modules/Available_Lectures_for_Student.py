from Attendance import app
from Attendance.models import UserStudents

with app.app_context():
    student = input("Please Enter the Student Registration No.:")
    x = UserStudents.query.filter_by(Registration_No_Student=student).first()
    y = x.Allotted_Lecture_to_Student
    if y:
        print("Available Lectures:")
        for lecture in y:
            print(lecture.Lecture_ID)
    else:
        print("No Lectures Available.")
