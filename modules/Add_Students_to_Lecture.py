from Attendance import app, db
from Attendance.models import LectureFormat, Course, UserStudents, LectureRecordsStudent, QrDataModel, AttendanceProcess

with app.app_context():
    lecture_id = input("Please enter Lecture ID: ")
    lecture = LectureFormat.query.filter_by(Lecture_ID=lecture_id).first()

    # Get the course associated with the lecture
    course_id = lecture.Lecture_Course  # This is the Course_ID (integer)

    # Retrieve the full Course object using the Course_ID
    course = Course.query.filter_by(Course_ID=course_id).first()

    # Get the enrolled students in the course
    enrolled_students = course.Enrolled_Students_In_Course

    already_added_students = []
    newly_added_students = []
    conflicting_students = []

    for student_record in enrolled_students:
        reg = student_record.Registration_No_Student
        student = UserStudents.query.filter_by(Registration_No_Student=reg).first()

        # Check if the student is already added to the lecture
        existing_entry = db.session.query(LectureRecordsStudent).filter_by(
            Lecture_ID=lecture_id, Lecture_Student_Reg=reg).first()

        if existing_entry:
            # If student already added, log them as already added
            already_added_students.append(student.Registration_No_Student)
        else:
            # Check if the student is enrolled in another lecture of the same course
            conflicting_lecture_entry = db.session.query(LectureRecordsStudent).join(LectureFormat).filter(
                LectureRecordsStudent.c.Lecture_Student_Reg == reg,
                LectureFormat.Lecture_Course == course.Course_ID
            ).first()

            if conflicting_lecture_entry:
                # If the student is already in another lecture of the same course, add to conflicting list
                conflicting_students.append(student.Registration_No_Student)
            else:
                # If student is not already added, add them to the lecture
                lecture.Lecture_Students.append(student)
                newly_added_students.append(student.Registration_No_Student)

                # Make a Qr Data Field For the student in QrDataModel
                qr = QrDataModel(QR_Registration_No_Student=reg,
                                 QR_Lecture_ID=lecture_id)

                db.session.add(qr)

                # Make a process holder for Student
                student_new_process = AttendanceProcess(
                    Process_Registration_No_Student=reg,
                    Process_Lecture_ID=lecture_id)

                db.session.add(student_new_process)

        # Commit the changes to the database
        db.session.commit()

    # Print results
    if newly_added_students:
        print("Newly Added Students: ")
        for student in newly_added_students:
            print(f"- {student}")

    if already_added_students:
        print("Students already added (duplicates): ")
        for student in already_added_students:
            print(f"- {student}")

    if conflicting_students:
        print("Students already enrolled in another lecture of the same course: ")
        for student in conflicting_students:
            print(f"- {student}")

    print("I have processed all students for this lecture.")
