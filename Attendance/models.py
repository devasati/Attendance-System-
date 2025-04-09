from Attendance import db, bcrypt, login_manager
from flask_login import UserMixin
import uuid

# Used user_students.Registration_No_Student, course.Course_ID, course.Course_Code because when we create
# database then the model is stored in this name format. See this in DB Browser.
# Described Before UserStudents so that can be used in defining the relationship.
Registered_Students_In_Courses = db.Table('Registered_Students_In_Courses',
                                          db.Column('Registration_No_Student', db.String(length=20),
                                                    db.ForeignKey('user_students.Registration_No_Student')),
                                          db.Column('Course_ID', db.Integer(), db.ForeignKey('course.Course_ID'))
                                          )


# Course list
class Course(db.Model):
    Course_ID = db.Column(db.Integer(), primary_key=True)
    Course_Code = db.Column(db.String(length=30), nullable=False, unique=True)
    Course_Name = db.Column(db.String(length=100), nullable=False, unique=True)
    Course_Type = db.Column(db.String(length=15), nullable=False)
    Course_Credits = db.Column(db.Integer(), nullable=False)
    Course_Lectures = db.relationship('LectureFormat', backref='Available_Course_for_Lecture')


# login manager for Student and Faculty
@login_manager.user_loader
def load_user(user_stu_fac):
    # First, try to load as a Student
    user = UserStudents.query.get(user_stu_fac)
    if user:
        return user

    # If not a student, try loading as Faculty
    user = UserFaculty.query.get(user_stu_fac)
    return user


# Students Data
class UserStudents(db.Model, UserMixin):
    Registration_No_Student = db.Column(db.String(length=20), nullable=False, primary_key=True)
    UserName_Student = db.Column(db.String(length=30), nullable=False, unique=True)
    Name_Student = db.Column(db.String(length=100), nullable=False)
    Branch_Student = db.Column(db.String(length=25), nullable=False)
    Email_Address_Student = db.Column(db.String(length=75), nullable=False, unique=True)
    Password_Hash_Student = db.Column(db.String(length=60), nullable=False)
    Registered_Courses = db.relationship('Course', secondary=Registered_Students_In_Courses,
                                         backref='Enrolled_Students_In_Course')

    @property
    def password(self):
        return self.password

    # For encrypting the password by user, the password from routes comes to setter for hashing and stored
    # in Password_Hash_Student
    @password.setter
    def password(self, plain_text_password):
        self.Password_Hash_Student = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    # At time of login, Used this to check whether the input password is matched with the stored hashed
    # password in the database model. Done by using bcrpyt function.
    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.Password_Hash_Student, attempted_password)

    # Overide method in UserMixin, because unable to get response by using it from there.
    def get_id(self):
        return self.Registration_No_Student  # Return the unique identifier


# Qr Code Storage Model
class QrDataModel(db.Model):
    Qr_ID = db.Column(db.String(10), primary_key=True, default=lambda: str(uuid.uuid4()))
    QR_Registration_No_Student = db.Column(db.String(length=20),
                                           db.ForeignKey('user_students.Registration_No_Student'))
    QR_Lecture_ID = db.Column(db.String(length=20), db.ForeignKey('lecture_format.Lecture_ID'))
    QR_Date = db.Column(db.String(length=20), default="")
    QR_Secret_Code = db.Column(db.Integer(), default=0)


# Faculty Data
class UserFaculty(db.Model, UserMixin):
    Employee_No_Faculty = db.Column(db.String(length=20), nullable=False, primary_key=True)
    UserName_Faculty = db.Column(db.String(length=30), nullable=False, unique=True)
    Name_Faculty = db.Column(db.String(length=100), nullable=False)
    Dept_Faculty = db.Column(db.String(length=25), nullable=False)
    Email_Address_Faculty = db.Column(db.String(length=75), nullable=False, unique=True)
    Password_Hash_Faculty = db.Column(db.String(length=60), nullable=False)
    Faculty_Lectures = db.relationship('LectureFormat', backref='Allotted_Faculty_for_Lecture')

    @property
    def password_faculty(self):
        return self.password_faculty

    # For encrypting the password by user, the password from routes comes to setter for hashing and stored
    # in Password_Hash_Faculty
    @password_faculty.setter
    def password_faculty(self, plain_text_password_faculty):
        self.Password_Hash_Faculty = bcrypt.generate_password_hash(plain_text_password_faculty).decode('utf-8')

    # At time of login, Used this to check whether the input password is matched with the stored hashed
    # password in the database model. Done by using bcrpyt function.
    def check_password_faculty_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.Password_Hash_Faculty, attempted_password)

    # Overide method in UserMixin, because unable to get response by using it from there.
    def get_id(self):
        return self.Employee_No_Faculty  # Return the unique identifier


# Students in a Lecture
LectureRecordsStudent = db.Table('LectureRecordsStudent',
                                 db.Column('Lecture_ID', db.String(length=20),
                                           db.ForeignKey('lecture_format.Lecture_ID')),
                                 db.Column('Lecture_Student_Reg', db.String(length=20),
                                           db.ForeignKey('user_students.Registration_No_Student')),
                                 db.UniqueConstraint('Lecture_ID', 'Lecture_Student_Reg',
                                                     name='unique_lecture_student')
                                 )


# Lecture Format Data, which tells about lecture execution
class LectureFormat(db.Model):
    Lecture_ID = db.Column(db.String(length=20), nullable=False, primary_key=True)
    Lecture_Slots = db.Column(db.String(length=20), nullable=False)
    Lecture_Course = db.Column(db.Integer(), db.ForeignKey('course.Course_ID'))
    Lecture_Faculty = db.Column(db.String(length=20), db.ForeignKey('user_faculty.Employee_No_Faculty'))
    Lecture_Students = db.relationship('UserStudents', secondary=LectureRecordsStudent,
                                       backref='Allotted_Lecture_to_Student')


# Model to tell whether attendance started or not
class AttendancePermission(db.Model):
    Lecture_To_Permitted = db.Column(db.String(length=20), db.ForeignKey('lecture_format.Lecture_ID'),
                                     primary_key=True)
    Lecture_Permission_Status = db.Column(db.Boolean(), default=False)


# Attendance Process Execution Status holder
class AttendanceProcess(db.Model):
    Process_ID = db.Column(db.String(10), primary_key=True, default=lambda: str(uuid.uuid4()))
    Process_Registration_No_Student = db.Column(db.String(length=20),
                                                db.ForeignKey('user_students.Registration_No_Student'))
    Process_Lecture_ID = db.Column(db.String(length=20), db.ForeignKey('lecture_format.Lecture_ID'))
    Process_Qr_Status = db.Column(db.Boolean(), default=False)
    Process_Face_Status = db.Column(db.Boolean(), default=False)


# Model to store Attendance
class AttendanceRecord(db.Model):
    Attendance_ID = db.Column(db.Integer(), primary_key=True)
    Attendance_Lecture = db.Column(db.String(length=20), db.ForeignKey('lecture_format.Lecture_ID'))
    Attendance_Student_Reg = db.Column(db.String(length=20), db.ForeignKey('user_students.Registration_No_Student'))
    Attendance_Date = db.Column(db.String(length=20), nullable=False)
    Attendance_Time = db.Column(db.String(length=20), nullable=False)
    Attendance_Slot = db.Column(db.String(length=20), nullable=False)
    Attendance_Status = db.Column(db.String(length=20), nullable=False)
