from flask import Flask, request, redirect, url_for, render_template, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import secrets
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///poc.db'
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

db = SQLAlchemy(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)

class JobPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('jobs', lazy=True))

@app.route('/')
def home():
    return render_template('register.html')

@app.route('/match', methods=['GET'])
def match():
    students = Student.query.all()
    jobs = JobPost.query.all()
    matches = []
    for student in students:
        for job in jobs:
            if 'Python' in job.description:
                matches.append((student.name, job.title))
    return render_template('match.html', matches=matches)

@app.route('/export', methods=['GET'])
def export_data():
    students = Student.query.all()
    jobs = JobPost.query.all()
    student_data = [(s.name, s.email) for s in students]
    job_data = [(j.title, j.description) for j in jobs]
    df_students = pd.DataFrame(student_data, columns=['Name', 'Email'])
    df_jobs = pd.DataFrame(job_data, columns=['Title', 'Description'])
    df_students.to_csv('students.csv', index=False)
    df_jobs.to_csv('jobs.csv', index=False)
    return render_template('export.html')

# Query Students
@app.route('/query_students', methods=['GET', 'POST'])
def query_students():
    if request.method == 'POST':
        email = request.form['email']
        student = Student.query.filter_by(email=email).first()
        return render_template('query_results.html', results=[student] if student else [], query='Student')
    return render_template('query_students.html')

# Query Jobs
@app.route('/query_jobs', methods=['GET', 'POST'])
def query_jobs():
    if request.method == 'POST':
        title = request.form['title']
        jobs = JobPost.query.filter(JobPost.title.like(f'%{title}%')).all()
        return render_template('query_results.html', results=jobs, query='Job')
    return render_template('query_jobs.html')

@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        if Student.query.filter_by(email=email).first():
            flash('Student already registered.')
        else:
            student = Student(email=email, name=name)
            db.session.add(student)
            db.session.commit()
            flash('Student registered successfully.')
        return redirect(url_for('home'))
    return render_template('register_student.html')

@app.route('/register_company', methods=['GET', 'POST'])
def register_company():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        if Company.query.filter_by(email=email).first():
            flash('Company already registered.')
        else:
            company = Company(email=email, name=name)
            db.session.add(company)
            db.session.commit()
            flash('Company registered successfully.')
        return redirect(url_for('home'))
    return render_template('register_company.html')

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        company_id = request.form['company_id']
        job = JobPost(title=title, description=description, company_id=company_id)
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully.')
        return redirect(url_for('home'))
    companies = Company.query.all()
    return render_template('post_job.html', companies=companies)

@app.route('/upload_cv', methods=['GET', 'POST'])
def upload_cv():
    if request.method == 'POST':
        if 'cv' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['cv']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('CV uploaded successfully.')
            return redirect(url_for('home'))
    return render_template('upload_cv.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'doc', 'docx'}

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    db.create_all()
    app.run(debug=True)
