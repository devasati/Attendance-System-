from Attendance import app, db
from flask import render_template, redirect, url_for, flash, request, make_response
from Attendance.forms import RegisterFormFaculty, LoginFormFaculty
from Attendance.models import UserFaculty, LectureFormat, AttendancePermission, QrDataModel, \
    AttendanceProcess, AttendanceRecord
from flask_login import login_user, logout_user, login_required, current_user
import datetime, random
import pandas as pd
from io import BytesIO


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
@login_required
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
