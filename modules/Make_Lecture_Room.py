from Attendance import app, db
from Attendance.models import LectureFormat, Course, UserFaculty, AttendancePermission

with app.app_context():
    lecture_id = input("Please enter Lecture ID: ")
    lecture_slots = input("Please enter Lecture Slots: ")
    course_id = int(input("Please enter Course ID for Lecture: "))
    faculty_id = input("Please enter Faculty ID for Lecture: ")

    course = Course.query.filter_by(Course_ID=course_id).first()
    faculty = UserFaculty.query.filter_by(Employee_No_Faculty=faculty_id).first()

    final = LectureFormat(Lecture_ID=lecture_id, Lecture_Slots=lecture_slots, Available_Course_for_Lecture=course,
                          Allotted_Faculty_for_Lecture=faculty)
    db.session.add(final)
    db.session.commit()

    new_attendance_permission = AttendancePermission(
        Lecture_To_Permitted = lecture_id
    )
    db.session.add(new_attendance_permission)
    db.session.commit()

