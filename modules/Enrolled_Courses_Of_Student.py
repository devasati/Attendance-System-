from Attendance.models import UserStudents
from Attendance import app

with app.app_context():
    student = input("Please enter Reg. No.: ")

    registration_no = UserStudents.query.filter_by(Registration_No_Student=student).first()

    x = registration_no.Registered_Courses

    for i in x:
        print(i)
