from Attendance import app, db
from flask import render_template, redirect, url_for, flash, request, jsonify, make_response
from Attendance.forms import RegisterFormStudent, LoginFormStudent, RegisterFormFaculty, LoginFormFaculty
from Attendance.models import UserStudents, UserFaculty, Course, LectureFormat, AttendancePermission, QrDataModel, \
    AttendanceProcess, AttendanceRecord
from flask_login import login_user, logout_user, login_required, current_user
import datetime, random
from modules.Qr_Generator import generate_qr
from modules.Qr_Checker import checker_qr_code
from modules.Face_Checker import process
from modules.image_saver import save_image
from modules.face_extractor_for_saving import extract_face_from_image
from modules.feature_extractor import extract_and_save_features
import cv2
import numpy as np
import pandas as pd
from io import BytesIO

# ---------**********-----------
# Changed for Deployment
import sys
from pathlib import Path

spoofing_path = Path(__file__).parent.parent / "modules" / "Silent-Face-Anti-Spoofing-master"
sys.path.append(str(spoofing_path))
from test_util import test


# ----------**********-----------

# Main Entrance Page of website
@app.route('/')
@app.route('/VITrack')
def entrance_page():
    return render_template('m11_Entrance.html')


# STUDENT ROUTES
# Login route for student
@app.route('/Login_Student', methods=['GET', 'POST'])
def login_student_page():
    form = LoginFormStudent()
    if form.validate_on_submit():
        attempted_user = UserStudents.query.filter_by(UserName_Student=form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(
                attempted_password=form.password.data
        ):
            login_user(attempted_user)
            flash(f'Success! You are logged in as: {attempted_user.Name_Student}', category='success')
            return redirect(url_for('home_student_page'))
        else:
            flash('Username and password are not match! Please try again', category='danger')

    return render_template('a21_Login_Student.html', form=form)


# Register route for student
@app.route('/Register_Student', methods=['GET', 'POST'])
def register_student_page():
    form = RegisterFormStudent()
    if form.validate_on_submit():
        user_to_create = UserStudents(Registration_No_Student=form.registration_no.data,
                                      UserName_Student=form.username.data,
                                      Name_Student=form.name.data,
                                      Branch_Student=form.branch.data,
                                      Email_Address_Student=form.email_address.data,
                                      password=form.password1.data)
        with app.app_context():
            db.session.add(user_to_create)
            db.session.commit()
        return redirect(url_for('login_student_page'))

    if form.errors != {}:  # If there are no errors from the validations
        for err_msg in form.errors.values():
            flash(f'There was an error with creating a user: {err_msg}', category='danger')

    return render_template('a22_Register_Student.html', form=form)


# Logout route for student
@app.route('/Logout_Student')
def logout_student_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("entrance_page"))


# Home Page for Student
@app.route('/Home_Student', methods=['GET', 'POST'])
def home_student_page():
    student = UserStudents.query.filter_by(Registration_No_Student=current_user.Registration_No_Student
                                           ).first()
    course_list = student.Registered_Courses

    if request.method == 'POST':
        course_req = request.form['course_id']

        with app.app_context():
            stu = UserStudents.query.filter_by(Registration_No_Student=current_user.Registration_No_Student
                                               ).first()
            cou = Course.query.filter_by(Course_ID=course_req).first()
            student_lec = stu.Allotted_Lecture_to_Student
            course_lec = cou.Course_Lectures
            result = list(set(student_lec) & set(course_lec))
            if result:
                # Have to iterate the list even if single element present, to get Lecture ID.
                for alpha in result:
                    send = alpha
                    send_final = send.Lecture_ID
                return redirect(url_for('lecture_student_page', lecture_record=send_final))
            else:
                return redirect(url_for('no_lecture_student_page'))

    return render_template('a31_Home_Student.html', course_list=course_list)


# Lecture Page when student has been assigned a class/lecture.
@app.route('/Lecture_Page_Student/<lecture_record>', methods=['GET', 'POST'])
def lecture_student_page(lecture_record):
    date = datetime.date.today()
    student_no = current_user.Registration_No_Student

    # Trying to get the Course object from the lecture ID we have
    lecture = LectureFormat.query.filter_by(Lecture_ID=lecture_record).first()
    course_in_lecture = lecture.Available_Course_for_Lecture
    courseinfo = course_in_lecture

    if request.method == 'POST':
        with app.app_context():
            lecture_for_permission = AttendancePermission.query.filter_by(Lecture_To_Permitted=lecture_record).first()
            permission = lecture_for_permission.Lecture_Permission_Status  # Getting the permission status on button click
            if permission:
                return redirect(url_for('qr_attendance_student_page', lecture_record=lecture_record,
                                        date_today=date, student_no=student_no))
            else:
                return redirect(url_for('no_attendance_student_page', lecture_record=lecture_record,
                                        date_today=date))

    return render_template('a31a_Lecture_Page_Student.html', courseinfo=courseinfo,
                           date=date, lecture_record=lecture_record)


# No Attendance Page for student, when student has been assigned a class/lecture.
# Used when Permission is not given
@app.route('/No_Attendance_Page_Student/<lecture_record>/<date_today>', methods=['GET', 'POST'])
def no_attendance_student_page(lecture_record, date_today):  # For a particular Course on a particular Date
    return render_template('a31a2_No_Attendance_Page_Student.html')


# QR Attendance Page for student, when student has been assigned a class/lecture.
# Used when Permission is given
@app.route('/QR_Attendance_Page_Student/<lecture_record>/<date_today>/<student_no>',
           methods=['GET', 'POST'])
def qr_attendance_student_page(lecture_record, date_today, student_no):
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'status': 'error', 'message': 'No data received'}), 400

            qr_data = data.get('qr_data')
            if not qr_data:
                return jsonify({'status': 'error', 'message': 'No QR data received'}), 400

            # Check Permission
            permission = AttendancePermission.query.filter_by(Lecture_To_Permitted=lecture_record).first()
            if permission:
                # Get Qr Data from Database
                qr_stored = QrDataModel.query.filter_by(QR_Lecture_ID=lecture_record,
                                                        QR_Registration_No_Student=student_no).first()
                if not qr_stored:
                    return jsonify(
                        {'status': 'error', 'message': 'No QR record found for this student and lecture'}), 404

                # Check the Qr
                result = checker_qr_code(qr_data,
                                         qr_stored.Qr_ID,
                                         qr_stored.QR_Registration_No_Student,
                                         qr_stored.QR_Lecture_ID,
                                         qr_stored.QR_Date,
                                         qr_stored.QR_Secret_Code)

                # Case 1: Success to Match Data in given time
                if result:
                    qr_status_update = AttendanceProcess.query.filter_by(Process_Lecture_ID=lecture_record,
                                                                         Process_Registration_No_Student=student_no).first()
                    qr_status_update.Process_Qr_Status = result
                    db.session.commit()
                    return jsonify({
                        'status': 'success',
                        'message': 'QR recorded successfully! Redirecting...',
                        'data': {
                            'lecture_record': lecture_record,
                            'date': date_today,
                            'student_no': student_no
                        }
                    })
                # Case 2: Failed to Match Data in given time
                else:
                    qr_status_update = AttendanceProcess.query.filter_by(Process_Lecture_ID=lecture_record,
                                                                         Process_Registration_No_Student=student_no).first()
                    qr_status_update.Process_Qr_Status = result
                    db.session.commit()
                    return jsonify(
                        {'status': 'error', 'message': 'QR code validation unsuccessful! Incorrect QR code used.'}), 400
            else:
                return jsonify(
                    {'status': 'error', 'message': 'Attendance time has expired. The allotted time has ended.'}), 404

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Failed to record attendance: {str(e)}'
            }), 500

    return render_template('a31a1_QR_Attendance_Page_Student.html',
                           lecture_record=lecture_record, date_today=date_today, student_no=student_no)


# Face Attendance Page for student, when student have successfully done qr scan.
@app.route('/Face_Attendance_Page_Student/<lecture_record>/<date_today>/<student_no>',
           methods=['GET', 'POST'])
def face_attendance_student_page(lecture_record, date_today, student_no):
    if request.method == 'GET':
        return render_template('a31a1_Face_Attendance_Page_Student.html',
                               lecture_record=lecture_record, date_today=date_today, student_no=student_no)

    elif request.method == 'POST':
        try:
            # Get the image file from the request
            if 'image' not in request.files:
                return jsonify({"success": False, "message": "No image file provided"})

            image_file = request.files['image']
            student_no = request.form.get('student_no')
            lecture_record = request.form.get('lecture_record')
            date_today = request.form.get('date_today')

            if image_file.filename == '':
                return jsonify({"success": False, "message": "No selected file"})

            if not image_file.content_type.startswith('image/'):
                return jsonify({"success": False, "message": "Uploaded file is not an image"})

            # Read image data without saving to disk
            in_memory_file = BytesIO()
            image_file.save(in_memory_file)
            data = np.frombuffer(in_memory_file.getvalue(), dtype=np.uint8)
            image = cv2.imdecode(data, cv2.IMREAD_COLOR)

            if image is None:
                return jsonify({"success": False, "message": "Failed to decode image"})

            # Process the image for face recognition
            recognized_names = process(image)

            # Check Permission
            permission = AttendancePermission.query.filter_by(Lecture_To_Permitted=lecture_record).first()

            if permission:

                # Case 1: Success to Match Image in given time
                if student_no in recognized_names:

                    # Check for Spoofing
                    label = test(image=image,
                                 model_dir='./modules/Silent-Face-Anti-Spoofing-master/resources/anti_spoof_models',
                                 device_id=0)

                    # Case 1a: If Not Spoof
                    if label == 1:
                        face_status_update = AttendanceProcess.query.filter_by(Process_Lecture_ID=lecture_record,
                                                                               Process_Registration_No_Student=student_no).first()
                        face_status_update.Process_Face_Status = 1
                        db.session.commit()

                        return jsonify({
                            "success": True,
                            "message": "Attendance recorded successfully.",
                            "student_no": student_no,
                            "lecture": lecture_record,
                            "date": date_today
                        })

                    # Case 1b: If Spoof
                    else:
                        face_status_update = AttendanceProcess.query.filter_by(Process_Lecture_ID=lecture_record,
                                                                               Process_Registration_No_Student=student_no).first()
                        face_status_update.Process_Face_Status = 0
                        db.session.commit()

                        return jsonify({"success": False, "message": "You are trying to Spoof."})

                # Case 2: Failed to Match Image in given time
                else:
                    face_status_update = AttendanceProcess.query.filter_by(Process_Lecture_ID=lecture_record,
                                                                           Process_Registration_No_Student=student_no).first()
                    face_status_update.Process_Face_Status = 0
                    db.session.commit()

                    return jsonify({"success": False, "message": "Face not recognized or Unknown Face"})

            else:
                face_status_update = AttendanceProcess.query.filter_by(Process_Lecture_ID=lecture_record,
                                                                       Process_Registration_No_Student=student_no).first()
                face_status_update.Process_Face_Status = 0
                db.session.commit()

                return jsonify(
                    {"success": False, "message": "'Attendance time has expired. The allotted time has ended."})

        except Exception as e:
            return jsonify({"success": False, "message": str(e)})


# Final Confirmation page after Attendance is completed successfully.
@app.route('/Attendance_Confirmation_Page_Student/<lecture_record>/<date_today>/<student_no>',
           methods=['GET', 'POST'])
def attendance_confirmation_page_student_page(lecture_record, date_today, student_no):
    return render_template('a31a11_Attendance_Confirmation_Page_Student.html',
                           lecture_record=lecture_record, date_today=date_today, student_no=student_no)


# No Lecture Page when student has not been assigned any class/lecture.
@app.route('/No_Lecture_Page_Student')
def no_lecture_student_page():
    return render_template('a31b_No_Lecture_Page_Student.html')


# Contact Support Page for student to get help, when student has not been assigned a class/lecture.
@app.route('/Contact_Support_Student')
def contact_support_student_page():
    return render_template('a31b1_Contact_Support_Student.html')


# Profile page of Student
@app.route('/Profile_Student', methods=['GET', 'POST'])
@login_required  # Ensure the user is logged in before accessing this route
def profile_student_page():
    return render_template('a32_Profile_Student.html')


# Scan section, Used to redirect to scan page
@app.route('/Scan_Student')
def scan_student_page():
    user = current_user.Registration_No_Student
    return render_template('a33_Scan_Student.html', user=user)


# Face scan page to save the face data of student
@app.route('/Face_Register_Student/<student_no>', methods=['GET', 'POST'])
def face_register_student_page(student_no):
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'capture':
            if 'image' not in request.files:
                return jsonify({'success': False, 'message': 'No image file received'}), 400

            image_file = request.files['image']
            image_file = extract_face_from_image(image_file)

            x = save_image(student_no, image_file)
            if x:
                # Return success response
                return jsonify({'success': True, 'message': 'Image received successfully'}), 200

            else:
                # Return failure response
                return jsonify({'success': False, 'message': 'Image NOT received successfully'}), 400

        elif action == 'complete':
            y = extract_and_save_features()

            if y:
                # Return success response
                return redirect(url_for("scan_student_page"))
            else:
                # Return failure response
                return jsonify({'success': False, 'message': 'Features not extracted successfully'}), 400

    return render_template('a33a_Face_Register_Student.html', student_no=student_no)


# Your Qr Page for displaying course and taking user to qr page to get qr
@app.route('/Your_Qr_Student', methods=['GET', 'POST'])
def your_qr_student_page():
    student = UserStudents.query.filter_by(Registration_No_Student=current_user.Registration_No_Student
                                           ).first()
    course_list = student.Registered_Courses

    if request.method == 'POST':
        course_req = request.form['course_id']

        stu = UserStudents.query.filter_by(Registration_No_Student=current_user.Registration_No_Student
                                           ).first()
        cou = Course.query.filter_by(Course_ID=course_req).first()
        student_lec = stu.Allotted_Lecture_to_Student
        course_lec = cou.Course_Lectures

        result = list(set(student_lec) & set(course_lec))

        if result:
            info = result[0].Lecture_ID  # Get the Lecture ID from the object
            return redirect(url_for(
                'qr_display_student_page', code_of_course=cou.Course_Code,
                student_reg_no=current_user.Registration_No_Student, id_of_lecture=info))
        else:
            return redirect(url_for('no_lecture_student_page'))

    return render_template('a34_Your_Qr_Student.html', course_list=course_list)


# QR Page to display the qr for a specific student and course of lecture till current date
@app.route('/Qr_Display_Student/<code_of_course>/<id_of_lecture>/<student_reg_no>', methods=['GET', 'POST'])
def qr_display_student_page(code_of_course, student_reg_no, id_of_lecture):
    course = Course.query.filter_by(Course_Code=code_of_course).first()
    lecture = id_of_lecture

    qr = QrDataModel.query.filter_by(QR_Lecture_ID=id_of_lecture,
                                     QR_Registration_No_Student=student_reg_no).first()

    # Getting Date and Image of Qr
    date_of_qr = qr.QR_Date
    qr_image = generate_qr(qr.Qr_ID,
                           qr.QR_Registration_No_Student,
                           qr.QR_Lecture_ID,
                           qr.QR_Date,
                           qr.QR_Secret_Code)

    return render_template('a34a_Qr_Display_Student.html', course=course, lecture=lecture,
                           date_of_qr=date_of_qr, qr_image=qr_image)


# Registration page for student to get enrolled in a course
@app.route('/Registration_Student', methods=['GET', 'POST'])
def registration_student_page():
    courses = Course.query.all()

    if request.method == 'POST':
        course = request.form['course_id']

        with app.app_context():
            x = current_user
            student = UserStudents.query.filter_by(Registration_No_Student=x.Registration_No_Student).first()
            course_selected = Course.query.filter_by(Course_ID=course).first()
            if course_selected in student.Registered_Courses:
                flash(f'You are already registered for {course_selected.Course_Name}.', category='warning')
            elif student and course_selected:
                db.session.add(course_selected)
                student.Registered_Courses.append(course_selected)
                db.session.commit()
                flash(f'Course {course_selected.Course_Name} is successfully registered.', category='success')
            else:
                flash("Server Down", category='danger')

    return render_template('a35_Registration_Student.html', courses=courses)


# Attendance History and records page.
@app.route('/Attendance_Records_Student', methods=['GET', 'POST'])
def attendance_records_student_page():
    user = UserStudents.query.filter_by(Registration_No_Student=current_user.Registration_No_Student).first()
    course_list = user.Registered_Courses

    if request.method == 'POST':
        course_req = request.form['course_id']

        stu = UserStudents.query.filter_by(Registration_No_Student=current_user.Registration_No_Student
                                           ).first()
        cou = Course.query.filter_by(Course_ID=course_req).first()
        student_lec = stu.Allotted_Lecture_to_Student
        course_lec = cou.Course_Lectures

        result = list(set(student_lec) & set(course_lec))
        if result:
            info = result[0].Lecture_ID  # Get the Lecture ID from the object
            return redirect(url_for(
                'records_page_student_page', code_course=cou.Course_Code,
                student_reg_no=current_user.Registration_No_Student, lecture_id=info))
        else:
            return redirect(url_for('no_lecture_student_page'))

    return render_template('a36_Attendance_Records_Student.html', course_list=course_list)


# Course attendance records page.
@app.route('/Records_Page_Student/<code_course>/<lecture_id>/<student_reg_no>', methods=['GET', 'POST'])
def records_page_student_page(code_course, student_reg_no, lecture_id):
    records = AttendanceRecord.query.filter_by(Attendance_Lecture=lecture_id,
                                               Attendance_Student_Reg=student_reg_no).all()
    return render_template('a36a_Records_Page_Student.html', records=records)


# FACULTY ROUTES
# Login route for faculty
@app.route('/Login_Faculty', methods=['GET', 'POST'])
def login_faculty_page():
    form = LoginFormFaculty()
    if form.validate_on_submit():
        attempted_user = UserFaculty.query.filter_by(UserName_Faculty=form.username_faculty.data).first()
        if attempted_user and attempted_user.check_password_faculty_correction(
                attempted_password=form.password3.data
        ):
            login_user(attempted_user)
            flash(f'Success! You are logged in as: {attempted_user.Name_Faculty}', category='success')
            return redirect(url_for('home_faculty_page'))
        else:
            flash('Username and password are not match! Please try again', category='danger')

    return render_template('b21_Login_Faculty.html', form=form)


# Register route for faculty
@app.route('/Register_Faculty', methods=['GET', 'POST'])
def register_faculty_page():
    form = RegisterFormFaculty()
    if form.validate_on_submit():
        user_to_create = UserFaculty(Employee_No_Faculty=form.employee_no_faculty.data,
                                     UserName_Faculty=form.username_faculty.data,
                                     Name_Faculty=form.name_faculty.data,
                                     Dept_Faculty=form.dept_faculty.data,
                                     Email_Address_Faculty=form.email_address_faculty.data,
                                     password_faculty=form.password3.data)
        with app.app_context():
            db.session.add(user_to_create)
            db.session.commit()
        return redirect(url_for('login_faculty_page'))

    if form.errors != {}:  # If there are no errors from the validations
        for err_msg in form.errors.values():
            flash(f'There was an error with creating a user: {err_msg}', category='danger')

    return render_template('b22_Register_Faculty.html', form=form)


# Logout route for faculty
@app.route('/Logout_Faculty')
def logout_faculty_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("entrance_page"))


# Home Page for Faculty
@app.route('/Home_Faculty', methods=['GET', 'POST'])
def home_faculty_page():
    faculty = current_user.Employee_No_Faculty
    x = UserFaculty.query.filter_by(Employee_No_Faculty=faculty).first()
    faculty_lectures = x.Faculty_Lectures

    if request.method == 'POST':
        lecture_req = request.form['lecture_id']

        lecture = LectureFormat.query.filter_by(Lecture_ID=lecture_req).first()
        lecture_cour = lecture.Available_Course_for_Lecture
        cour = lecture_cour.Course_Code

        date = datetime.date.today()

        return redirect(url_for('attendance_page_faculty_page', lecture_id=lecture_req,
                                date_today=date, course=cour))

    return render_template('b31_Home_Faculty.html', faculty_lectures=faculty_lectures)


# Attendance Page of Faculty
@app.route('/Attendance_Page_Faculty/<lecture_id>/<course>/<date_today>', methods=['GET', 'POST'])
def attendance_page_faculty_page(lecture_id, date_today, course):
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'start':
            with app.app_context():
                # Allow the students to access the attendance page
                lecture_for_attendance = AttendancePermission.query.filter_by(Lecture_To_Permitted=lecture_id).first()
                lecture_for_attendance.Lecture_Permission_Status = True
                db.session.commit()

                # Get the Qr Code Details for the Model which stores the Qr Code
                def generate_random_number():
                    return random.randint(1000, 9999)

                random_number = generate_random_number()  # Get a random number
                date = datetime.date.today()  # Get current date

                # Update in database based on the lecture_id grabbed in function
                qr_lectures = QrDataModel.query.filter_by(QR_Lecture_ID=lecture_id).all()
                for qr_lecture in qr_lectures:
                    qr_lecture.QR_Secret_Code = random_number
                    qr_lecture.QR_Date = f"{date}"
                db.session.commit()

        elif action == 'stop':
            with app.app_context():

                # Change Permission to Not Allowed
                lecture_for_attendance = AttendancePermission.query.filter_by(Lecture_To_Permitted=lecture_id).first()
                lecture_for_attendance.Lecture_Permission_Status = False
                db.session.commit()

                # Get Current Time
                time = datetime.datetime.now().time().strftime(("%H:%M"))

                # Get lecture object for slots
                lecture = LectureFormat.query.filter_by(Lecture_ID=lecture_id).first()

                # Put the Attendance record in the Database
                status_records = AttendanceProcess.query.filter_by(Process_Lecture_ID=lecture_id).all()
                for x in status_records:

                    # Check if record already exist.
                    exist = AttendanceRecord.query.filter_by(Attendance_Lecture=x.Process_Lecture_ID,
                                                             Attendance_Student_Reg=x.Process_Registration_No_Student,
                                                             Attendance_Date=date_today,
                                                             ).all()
                    if exist:
                        continue

                    if x.Process_Qr_Status == 1 and x.Process_Face_Status == 1:
                        status = "Present"
                    else:
                        status = "Absent"

                    record = AttendanceRecord(Attendance_Lecture=x.Process_Lecture_ID,
                                              Attendance_Student_Reg=x.Process_Registration_No_Student,
                                              Attendance_Date=date_today,
                                              Attendance_Time=time,
                                              Attendance_Slot=lecture.Lecture_Slots,
                                              Attendance_Status=status)
                    db.session.add(record)
                    db.session.commit()

                # Reset Attendance Status Holder of Students
                process_status_records = AttendanceProcess.query.filter_by(Process_Lecture_ID=lecture_id).all()
                for x in process_status_records:
                    x.Process_Qr_Status = 0
                    x.Process_Face_Status = 0
                    db.session.commit()

    return render_template('b31a_Attendance_Page_Faculty.html', lecture_id=lecture_id,
                           date_today=date_today, course=course)


# Profile Page for Faculty
@app.route('/Profile_Faculty', methods=['GET', 'POST'])
def profile_faculty_page():
    return render_template('b32_Profile_Faculty.html')


# Edit Attendance Page for Faculty
@app.route('/Edit_Attendance_Faculty')
def edit_attendance_faculty_page():
    return render_template('b33_Edit_Attendance_Faculty.html')


# Attendance Page for Faculty
@app.route('/Attendance_View_Faculty', methods=['GET', 'POST'])
def attendance_view_faculty_page():
    faculty = current_user.Employee_No_Faculty
    x = UserFaculty.query.filter_by(Employee_No_Faculty=faculty).first()
    faculty_lectures = x.Faculty_Lectures

    if request.method == 'POST':
        lecture_req = request.form['lecture_id']
        return redirect(url_for('lecture_attendance_faculty_page', lecture_id=lecture_req))

    return render_template('b34_Attendance_View_Faculty.html', faculty_lectures=faculty_lectures)


# Attendance View of a Lecture
@app.route('/Lecture_Attendance_Faculty/<lecture_id>', methods=['GET', 'POST'])
def lecture_attendance_faculty_page(lecture_id):
    date_records = db.session.query(AttendanceRecord) \
        .filter_by(Attendance_Lecture=lecture_id) \
        .group_by(AttendanceRecord.Attendance_Date) \
        .all()

    if request.method == 'POST':
        date = request.form['date_selected']
        return redirect(url_for('date_lecture_attendance_faculty_page', lecture_id=lecture_id,
                                date_selected=date))

    return render_template('b34a_Lecture_Attendance_Faculty.html',
                           date_records=date_records, lecture_id=lecture_id)


# Attendance View of a Lecture on a day with download option
@app.route('/Date_Lecture_Attendance_Faculty/<lecture_id>/<date_selected>', methods=['GET', 'POST'])
def date_lecture_attendance_faculty_page(lecture_id, date_selected):
    stu_records = AttendanceRecord.query.filter_by(Attendance_Lecture=lecture_id, Attendance_Date=date_selected).all()

    if request.method == 'POST' and 'download' in request.form:

        data = []
        for record in stu_records:
            data.append({
                'Student Registration No.': record.Attendance_Student_Reg,
                'Attendance Time': record.Attendance_Time,
                'Attendance Slot': record.Attendance_Slot,
                'Attendance Status': record.Attendance_Status
            })

        df = pd.DataFrame(data)

        # Create Excel file in memory
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Attendance', index=False)
        writer.close()
        output.seek(0)

        response = make_response(output.getvalue())  # Create Flask response with Excel data
        response.headers[
            'Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  # Set MIME type
        response.headers[
            'Content-Disposition'] = f'attachment; filename=attendance_{lecture_id}_{date_selected}.xlsx'  # Set filename
        return response

    return render_template('b34aa_Date_Lecture_Attendance_Faculty.html',
                           stu_records=stu_records, lecture_id=lecture_id, date_selected=date_selected)
