from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Length, DataRequired, EqualTo, Email, ValidationError
from Attendance.models import UserStudents, UserFaculty


class RegisterFormStudent(FlaskForm):

    def validate_registration_no(self, registration_no_to_check):
        reg = UserStudents.query.filter_by(Registration_No_Student=registration_no_to_check.data).first()
        if reg:
            raise ValidationError('Registration No. already exists! Please try a different Registration No.')

    def validate_username(self, username_to_check):
        user = UserStudents.query.filter_by(UserName_Student=username_to_check.data).first()
        if user:
            raise ValidationError('Username already exists! Please try a different Username')

    def validate_email_address(self, email_address_to_check):
        email = UserStudents.query.filter_by(Email_Address_Student=email_address_to_check.data).first()
        if email:
            raise ValidationError('Email Address already exists! Please try a different Email Address')

    registration_no = StringField(label='Registration No.:', validators=[Length(min=10, max=10), DataRequired()])
    username = StringField(label='User Name:', validators=[Length(min=4), DataRequired()])
    name = StringField(label='Name:', validators=[Length(max=100), DataRequired()])
    branch = StringField(label='Branch Name:', validators=[Length(max=25), DataRequired()])
    email_address = StringField(label='Email Address:', validators=[Email(), DataRequired()])
    password1 = PasswordField(label='Password:', validators=[Length(min=6), DataRequired()])
    password2 = PasswordField(label='Confirm Password:', validators=[EqualTo('password1'), DataRequired()])
    submit = SubmitField(label='Create Account')


class LoginFormStudent(FlaskForm):
    username = StringField(label='User Name:', validators=[DataRequired()])
    password = PasswordField(label='Password:', validators=[DataRequired()])
    submit = SubmitField(label='Sign in')


class RegisterFormFaculty(FlaskForm):

    def validate_employee_no_faculty(self, employee_no_faculty_to_check):
        emn = UserFaculty.query.filter_by(Employee_No_Faculty=employee_no_faculty_to_check.data).first()
        if emn:
            raise ValidationError('Employee Number already exists! Please try a different Employee Number')

    def validate_username_faculty(self, username_faculty_to_check):
        e_user = UserFaculty.query.filter_by(UserName_Faculty=username_faculty_to_check.data).first()
        if e_user:
            raise ValidationError('Username already exists! Please try a different Username')

    def validate_email_address_faculty(self, email_address_faculty_to_check):
        emp_email = UserFaculty.query.filter_by(Email_Address_Faculty=email_address_faculty_to_check.data).first()
        if emp_email:
            raise ValidationError('Email Address already exists! Please try a different Email Address')

    employee_no_faculty = StringField(label='Employee Number:', validators=[Length(min=8, max=8), DataRequired()])
    username_faculty = StringField(label='User Name:', validators=[Length(min=4), DataRequired()])
    name_faculty = StringField(label='Name:', validators=[Length(max=100), DataRequired()])
    dept_faculty = StringField(label='Department Name:', validators=[Length(max=25), DataRequired()])
    email_address_faculty = StringField(label='Email Address:', validators=[Email(), DataRequired()])
    password3 = PasswordField(label='Password:', validators=[Length(min=6), DataRequired()])
    password4 = PasswordField(label='Confirm Password:', validators=[EqualTo('password3'), DataRequired()])
    submit_faculty = SubmitField(label='Create Account')


class LoginFormFaculty(FlaskForm):
    username_faculty = StringField(label='User Name:', validators=[DataRequired()])
    password3 = PasswordField(label='Password:', validators=[DataRequired()])
    submit_faculty = SubmitField(label='Sign in')

