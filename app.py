import io
import random
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for, flash, send_file)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user, logout_user, login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from openpyxl import Workbook
import qrcode
from flask_weasyprint import HTML, render_pdf


import os
# --- App Configuration ---
app = Flask(__name__)
# app.config['SECRET_KEY'] = 'a-very-secret-key-that-you-should-change'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///college.db'


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///local.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Database Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    roll_number = db.Column(db.String(50), nullable=True)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    lecture_type = db.Column(db.String(20), default='Lecture')
    duration = db.Column(db.Integer, default=1)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    teacher = db.relationship('User', backref='subjects_taught')

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)

class StudentGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class CourseAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))

class BlockedSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(20), nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'))
    reason = db.Column(db.String(100), nullable=True)

class TimeTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(20), nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    group = db.relationship('StudentGroup')
    subject = db.relationship('Subject')
    room = db.relationship('Room')
    teacher = db.relationship('User')

class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timetable_id = db.Column(db.Integer, db.ForeignKey('time_table.id'), nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

# --- Login Manager & Role Decorator ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def role_required(role):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash("You don't have permission to access this page.", "danger")
                return redirect(url_for('index'))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

# --- Authentication Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email, password, role = request.form['email'], request.form['password'], request.form['role']
        roll_number = request.form.get('roll_number')
        if User.query.filter_by(email=email).first():
            flash('Email address already exists.', 'danger')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(email=email, password=hashed_password, role=role, roll_number=roll_number)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email, password = request.form['email'], request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'admin': return redirect(url_for('admin_dashboard'))
            elif user.role == 'teacher': return redirect(url_for('teacher_dashboard'))
            else: return redirect(url_for('student_dashboard'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- Admin Routes ---
@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    selected_day = request.args.get('selected_day', 'Monday')
    teachers = User.query.filter_by(role='teacher').all()
    subjects = Subject.query.all()
    rooms = Room.query.all()
    groups = StudentGroup.query.all()
    time_slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00', '14:00-15:00', '15:00-16:00']
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    timetable_data = {day: {slot: {group.id: None for group in groups} for slot in time_slots} for day in days}
    for entry in TimeTable.query.all():
        if entry.day in timetable_data and entry.time_slot in timetable_data[entry.day]:
            timetable_data[entry.day][entry.time_slot][entry.group_id] = entry

    return render_template('admin_dashboard.html', teachers=teachers, subjects=subjects, 
                           rooms=rooms, groups=groups, timetable_data=timetable_data, 
                           days=days, time_slots=time_slots, selected_day=selected_day)

@app.route('/admin/add_room', methods=['POST'])
@login_required
@role_required('admin')
def add_room():
    db.session.add(Room(name=request.form['name'], capacity=request.form['capacity']))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_group', methods=['POST'])
@login_required
@role_required('admin')
def add_group():
    db.session.add(StudentGroup(name=request.form['name']))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_subject', methods=['POST'])
@login_required
@role_required('admin')
def add_subject():
    db.session.add(Subject(name=request.form['name'], code=request.form['code'], 
                           lecture_type=request.form['lecture_type'], duration=request.form['duration'],
                           teacher_id=request.form['teacher_id']))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/assign_course', methods=['POST'])
@login_required
@role_required('admin')
def assign_course():
    group_id = request.form['group_id']
    subject_ids = request.form.getlist('subject_ids')
    CourseAssignment.query.filter_by(group_id=group_id).delete()
    for subject_id in subject_ids:
        db.session.add(CourseAssignment(group_id=group_id, subject_id=subject_id))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_blocked_slot', methods=['POST'])
@login_required
@role_required('admin')
def add_blocked_slot():
    db.session.add(BlockedSlot(day=request.form['day'], time_slot=request.form['time_slot'],
                               group_id=request.form['group_id'], reason=request.form['reason']))
    db.session.commit()
    flash('Slot has been blocked successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_day_timetable', methods=['POST'])
@login_required
@role_required('admin')
def update_day_timetable():
    selected_day = request.form['day']
    groups = StudentGroup.query.all()
    time_slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00', '14:00-15:00', '15:00-16:00']
    
    new_entries, has_errors = [], False
    for slot in time_slots:
        occupied_teachers = set()
        for group in groups:
            subject_id = request.form.get(f'subject_{slot}_{group.id}')
            teacher_id = request.form.get(f'teacher_{slot}_{group.id}')
            room_id = request.form.get(f'room_{slot}_{group.id}')

            if subject_id and teacher_id and room_id:
                teacher_id, group_id = int(teacher_id), int(group.id)
                
                if teacher_id in occupied_teachers:
                    flash(f"Conflict: Teacher is double-booked at {slot} on {selected_day}.", "danger")
                    has_errors = True
                if BlockedSlot.query.filter_by(day=selected_day, time_slot=slot, group_id=group_id).first():
                    flash(f"Conflict: Slot {slot} for {group.name} is blocked.", "danger")
                    has_errors = True

                if has_errors: break
                occupied_teachers.add(teacher_id)
                new_entries.append(TimeTable(day=selected_day, time_slot=slot, group_id=group_id,
                                             subject_id=subject_id, teacher_id=teacher_id, room_id=room_id))
        if has_errors: break
            
    if not has_errors:
        TimeTable.query.filter_by(day=selected_day).delete()
        db.session.add_all(new_entries)
        db.session.commit()
        flash(f"Timetable for {selected_day} updated successfully!", "success")
    
    return redirect(url_for('admin_dashboard', selected_day=selected_day))

@app.route('/admin/generate_timetable')
@login_required
@role_required('admin')
def generate_timetable():
    TimeTable.query.delete()
    db.session.commit()
    flash('Placeholder auto-generator run. Timetable cleared.', 'info')
    return redirect(url_for('admin_dashboard'))

# --- NEW ROUTES FOR USER MANAGEMENT ---
@app.route('/admin/manage_users')
@login_required
@role_required('admin')
def manage_users():
    users = User.query.filter(User.role != 'admin').order_by(User.role).all()
    return render_template('manage_users.html', users=users)

@app.route('/admin/update_role/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def update_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in ['student', 'teacher']:
        user.role = new_role
        db.session.commit()
        flash(f"User {user.email}'s role has been updated to {new_role}.", "success")
    else:
        flash("Invalid role selected.", "danger")
    return redirect(url_for('manage_users'))

# --- Public Timetable Viewer and PDF Download ---
@app.route('/view-timetable', methods=['GET', 'POST'])
def view_timetable():
    all_groups = StudentGroup.query.order_by(StudentGroup.name).all()
    selected_group_id, selected_group_name, timetable_data = None, None, None
    time_slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00', '14:00-15:00', '15:00-16:00']
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    if request.method == 'POST':
        selected_group_id = int(request.form['group_id'])
        group = StudentGroup.query.get(selected_group_id)
        selected_group_name = group.name
        entries = TimeTable.query.filter_by(group_id=selected_group_id).all()
        
        timetable_data = {day: {} for day in days}
        for entry in entries:
            entry.is_spanned = False
            timetable_data[entry.day][entry.time_slot] = entry
        
        for day in days:
            for i, slot in enumerate(time_slots):
                entry = timetable_data[day].get(slot)
                if entry and entry.subject.duration > 1:
                    for j in range(1, entry.subject.duration):
                        if i + j < len(time_slots):
                            next_slot_key = time_slots[i + j]
                            if timetable_data[day].get(next_slot_key):
                                timetable_data[day][next_slot_key].is_spanned = True

    return render_template('view_timetable.html', all_groups=all_groups, 
                           selected_group_id=selected_group_id, selected_group_name=selected_group_name,
                           timetable_data=timetable_data, days=days, time_slots=time_slots)

@app.route('/download-pdf/<int:group_id>')
def download_pdf(group_id):
    group = StudentGroup.query.get_or_404(group_id)
    entries = TimeTable.query.filter_by(group_id=group_id).all()
    time_slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00', '14:00-15:00', '15:00-16:00']
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    timetable_data = {day: {} for day in days}
    for entry in entries:
        entry.is_spanned = False
        timetable_data[entry.day][entry.time_slot] = entry
    
    for day in days:
        for i, slot in enumerate(time_slots):
            entry = timetable_data[day].get(slot)
            if entry and entry.subject.duration > 1:
                for j in range(1, entry.subject.duration):
                    if i + j < len(time_slots):
                        if timetable_data[day].get(time_slots[i + j]):
                            timetable_data[day][time_slots[i + j]].is_spanned = True
    
    html = render_template('timetable_pdf.html', timetable_data=timetable_data, days=days,
                           time_slots=time_slots, group_name=group.name)
    return render_pdf(HTML(string=html))

# --- Teacher & Student Routes ---
@app.route('/teacher/dashboard')
@login_required
@role_required('teacher')
def teacher_dashboard():
    schedule = TimeTable.query.filter_by(teacher_id=current_user.id).order_by(TimeTable.day, TimeTable.time_slot).all()
    return render_template('teacher_dashboard.html', schedule=schedule)
    
@app.route('/student/dashboard')
@login_required
@role_required('student')
def student_dashboard():
    schedule = TimeTable.query.all()
    attendance = AttendanceRecord.query.filter_by(student_id=current_user.id).all()
    percentage = (len(attendance) / len(schedule) * 100) if schedule else 0
    return render_template('student_dashboard.html', percentage=round(percentage, 2))

@app.route('/generate-qr/<int:timetable_id>')
@login_required
@role_required('teacher')
def generate_qr(timetable_id):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    token = s.dumps({'timetable_id': timetable_id}, salt='attendance-qr')
    img_buf = io.BytesIO()
    qrcode.make(token).save(img_buf)
    img_buf.seek(0)
    return send_file(img_buf, mimetype='image/png')
    
@app.route('/mark-attendance', methods=['POST'])
@login_required
@role_required('student')
def mark_attendance():
    token = request.form['qr_token']
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token, salt='attendance-qr', max_age=600)
        timetable_id = data['timetable_id']
        if not AttendanceRecord.query.filter_by(student_id=current_user.id, timetable_id=timetable_id).first():
            db.session.add(AttendanceRecord(student_id=current_user.id, timetable_id=timetable_id))
            db.session.commit()
            flash('Attendance marked successfully!', 'success')
        else:
            flash('Attendance already marked for this class.', 'warning')
    except Exception:
        flash('Failed: Invalid or expired QR code.', 'danger')
    return redirect(url_for('student_dashboard'))
    
@app.route('/export_excel')
@login_required
def export_excel():
    records = db.session.query(User.roll_number, Subject.name, AttendanceRecord.timestamp)\
        .join(User).join(TimeTable).join(Subject)\
        .filter(AttendanceRecord.student_id == current_user.id).all()

    wb, ws = Workbook(), Workbook().active
    ws.title = "Attendance Report"
    ws.append(['Roll Number', 'Subject', 'Timestamp'])
    for rec in records:
        ws.append([rec.roll_number, rec.name, rec.timestamp.strftime('%Y-%m-%d %H:%M:%S')])
    
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='attendance_report.xlsx')

# --- CLI Command ---
# @app.cli.command("init-db")
# def init_db():
#     db.create_all()
#     if not User.query.filter_by(role='admin').first():
#         hashed_password = generate_password_hash('adminpass', method='pbkdf2:sha256')
#         db.session.add(User(email='admin@college.com', password=hashed_password, role='admin'))
#         db.session.commit()
#         print("Database initialized and admin user created.")
#     else:
#         print("Database already initialized.")
# --- CLI Command ---
# @app.cli.command("init-db")
# def init_db():
#     db.create_all()
#     if not User.query.filter_by(role='admin').first():
#         admin_email = 'admin@college.com'
#         admin_password = 'adminpass'
#         hashed_password = generate_password_hash(admin_password, method='pbkdf2:sha256')
        
#         db.session.add(User(email=admin_email, password=hashed_password, role='admin'))
#         db.session.commit()
        
#         print("✅ Database initialized and admin user created.")
#         print(f"👉 Admin Email: {admin_email}")
#         print(f"👉 Admin Password: {admin_password}")
#     else:
#         print("⚠️ Database already initialized. Admin user already exists.")

@app.cli.command("init-db")
def init_db():
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        admin_email = 'admin@college.com'
        admin_password = 'adminpass'
        hashed_password = generate_password_hash(admin_password, method='pbkdf2:sha256')
        
        db.session.add(User(email=admin_email, password=hashed_password, role='admin'))
        db.session.commit()
        
        print("✅ Database initialized and admin user created.")
        print(f"👉 Admin Email: {admin_email}")
        print(f"👉 Admin Password: {admin_password}")
    else:
        print("⚠️ Database already initialized. Admin user already exists.")



if __name__ == '__main__':
    app.run(debug=True)