# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ---- Core Users ----
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin | teacher | student
    roll_number = db.Column(db.String(50), unique=True, nullable=True)  # students only
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'), nullable=True)  # students

class StudentGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)
    students = db.relationship('User', backref='group', lazy=True)

class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=40)
    lat = db.Column(db.Float, nullable=True)  # optional for geofence
    lng = db.Column(db.Float, nullable=True)



# class Subject(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(120), nullable=False)
#     code = db.Column(db.String(20), unique=True, nullable=False)
#     teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'), nullable=False)
#     freq_per_week = db.Column(db.Integer, nullable=False, default=2)  # e.g., 2 classes/week
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    code = db.Column(db.String(20))
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # or Teacher.id if you have Teacher table
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'))

    freq_per_week = db.Column(db.Integer, default=2)  # <-- add this

    teacher = db.relationship('User', backref='subjects')  # or Teacher
    group = db.relationship('StudentGroup', backref='subjects')




class TeacherAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    day = db.Column(db.String(10), nullable=False)       # "Mon".."Fri"
    time_slot = db.Column(db.String(20), nullable=False) # "09:00-10:00"

class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(10), nullable=False)
    time_slot = db.Column(db.String(20), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'), nullable=False)

    subject = db.relationship('Subject')
    teacher = db.relationship('User', foreign_keys=[teacher_id])
    classroom = db.relationship('Classroom')
    group = db.relationship('StudentGroup')

class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timetable_id = db.Column(db.Integer, db.ForeignKey('timetable.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    ip = db.Column(db.String(64), nullable=True)
