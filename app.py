import time
from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
# using flask
from timetable import create_timetable
import json
import os


app = Flask(__name__)

# Database config

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'scheduleDB'

# File paths

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, 'static', 'timetable.json')

mysql = MySQL(app)


#  The root page
@app.route('/')
def root():
    return render_template("login.html")


"""
Handles the login post request
Usernames:
Admin -> admin page
staff/<staffid> -> timetable view for that staff 
student/<studentid> -> timetable view for teaching group of that student 

Redirect back to root if no valid username
"""
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        form = request.form
        username = form['username']

        if username:
            username = username.lower()

            if username == "admin":
                return redirect(url_for('admin'))

            elif "/" in username:
                user_str = username.split("/")

                if user_str[0] == "student" and user_str[1].isnumeric():
                    group = getStudentClass(int(user_str[1]))
                    if group is not None:
                        return redirect('class/' + str(group[0]))

                elif user_str[0].lower() == "staff" and user_str[1].isnumeric():
                    return redirect('staff/' + user_str[1])

    return redirect(url_for('root'))


# Admin page
# Uses getter functions to supply data to html template using jinja
@app.route('/admin', methods=['POST', 'GET'])
def admin():
    return render_template('admin.html', classes=getClasses(), subjects=getSubjects(), teachers=getTeachers(), students=getStudents());


# Handles post request from "Add teacher form"
# Commits data to database
@app.route('/addteacher', methods=['GET', 'POST'])
def addTeacher():
    if request.method == 'POST':
        # Fetch form data
        teacherDetails = request.form
        firstName = teacherDetails['first-name']
        lastName = teacherDetails['last-name']
        phoneNumber = teacherDetails['phone-number']
        email = teacherDetails['email']
        address = teacherDetails['address']
        subjectId = teacherDetails['subject']
        workHours = teacherDetails['hours']

        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO teachers(first_name, last_name, phone, email, home_address, subject_id,hours_per_week)
                     VALUES(%s,%s,%s,%s,%s,%s,%s)''', (firstName, lastName, phoneNumber, email, address, subjectId, workHours))

        mysql.connection.commit();
        cur.close()
        return redirect(url_for('admin'))


# Handles post request from "Add subject form"
# Commits data to database
@app.route('/addsubject', methods=['GET', 'POST'])
def addSubject():
    if request.method == 'POST':
        # Fetch form data
        subjectDetails = request.form
        subjectName = subjectDetails['subject-name']
        subjectHours = subjectDetails['hours']

        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO subjects(subject_name, hours_per_week)
                     VALUES(%s,%s)''', (subjectName, subjectHours))

        mysql.connection.commit();
        cur.close()
        return redirect(url_for('admin'))


# Handles post request from "Add class form"
# Commits data to database
@app.route('/addclass', methods=['GET', 'POST'])
def addClass():
    if request.method == 'POST':
        # Fetch form data
        classDetails = request.form
        className = classDetails['class-name']

        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO class(class_name)
                     VALUES(%s)''', (className,))

        mysql.connection.commit();
        cur.close()
        return redirect(url_for('admin'))


# Handles post request from "Add student form"
# Commits data to database
@app.route('/addstudent', methods=['GET', 'POST'])
def addStudent():
    if request.method == 'POST':
        # Fetch form data
        studentDetails = request.form
        firstName = studentDetails['first-name']
        lastName = studentDetails['last-name']
        email = studentDetails['email']
        classId = studentDetails['class']

        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO students(first_name, last_name, email, class_id)
                     VALUES(%s,%s,%s,%s)''', (firstName, lastName, email, classId))

        mysql.connection.commit();
        cur.close()
        return redirect(url_for('admin'))


# Handles post request from "Create timetable button"
# Uses getter functions to supply data from database
# Converts these lists to json and saves it to timetable.json file
@app.route('/createTimetable', methods=['GET', 'POST'])
def createTimetable():
    if request.method == 'POST':

        subjects = {}
        teachers = {}
        classes = []
        for subject in getSubjects():
            subjects[subject[0]] = int(subject[2])
        for teacher in getTeachers():
            teachers[teacher[0]] = (int(teacher[4]), teacher[3])
        for group in getClasses():
            classes.append(group[0])

        schedule = create_timetable(classes, teachers, subjects)
        jsonString = json.dumps(schedule)
        jsonFile = open(json_url, "w")
        jsonFile.write(jsonString)
        jsonFile.close()

        return redirect(url_for('admin'))


# Displays the timetable for a specific teacher by id
# Inputs the current schedule from the timetable.json file and searches for maxes with that teacher id
# Appends the found events to array and returns jinja template with events
@app.route('/staff/<int:teacher_id>', methods=['GET', 'POST'])
def getTeacherSchedule(teacher_id):

    timetable = json.load(open(json_url))
    events = []
    for event in timetable:
        if event[1] == int(teacher_id):
            events.append((("Class: " + getClassName(event[0])[0]), getSubjectName(event[2]), time.strptime(event[3], "%A").tm_wday+1, event[4].split('-')[0], event[4].split('-')[1]))
    if events:
        return render_template("timetable.html", name=getTeacherName(teacher_id), events=events)
    else:
        return redirect(url_for('login'))


# Displays the timetable for a class by id
# Inputs the current schedule from the timetable.json file and searches for maxes with that class id
# Appends the found events to array and returns jinja template with events
@app.route('/class/<int:class_id>', methods=['GET', 'POST'])
def getClassSchedule(class_id):

    timetable = json.load(open(json_url))
    events = []
    for event in timetable:
        if event[0] == int(class_id):
            events.append((("Teacher: " + getTeacherName(event[1])[0][0] + " " + getTeacherName(event[1])[1]), getSubjectName(event[2]), time.strptime(event[3], "%A").tm_wday+1, event[4].split('-')[0], event[4].split('-')[1]))
    if events:
        return render_template("timetable.html", name=getClassName(class_id), events=events)
    else:
        return redirect(url_for('login'))


# Returns data from sql query
# takes id of student and gets their class
def getStudentClass(id):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT class_id FROM students WHERE student_id = %s''', (id,))
    group = cur.fetchone()
    cur.close()
    return group


# Returns data from sql query
# takes id of teacher and gets their fullname
def getTeacherName(id):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT first_name, last_name FROM teachers WHERE staff_id = %s''', (id,))
    teacher = cur.fetchone()
    cur.close()
    return teacher


# Returns data from sql query
# takes id of student and gets their fullname
def getStudentName(id):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT first_name, last_name FROM students WHERE student_id = %s''', (id,))
    student = cur.fetchone()
    cur.close()
    return student


# Returns data from sql query
# takes id of student and gets their class
def getClassName(id):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT class_name FROM class WHERE class_id = %s''',(id,))
    group = cur.fetchone()
    cur.close()
    return group


# Returns data from sql query
# takes id of student and gets their fullname
def getSubjectName(id):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT subject_name FROM subjects WHERE subject_id = %s''',(id,))
    subject = cur.fetchone()
    cur.close()
    return subject[0]


# Returns data from sql query
# gets full list of all subjects
def getSubjects():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT subject_id, subject_name, hours_per_week FROM subjects''')
    subjectList = cur.fetchall()
    cur.close()
    return subjectList


# Returns data from sql query
# gets full list of all classes
def getClasses():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT class_id, class_name FROM class''')
    classList = cur.fetchall()
    cur.close()
    return classList


# Returns data from sql query
# gets full list of all students
def getStudents():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT student_id, first_name, last_name FROM students''')
    studentList = cur.fetchall()
    cur.close()
    return studentList


# Returns data from sql query
# gets full list of all teachers
def getTeachers():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT staff_id, first_name, last_name,subject_id,hours_per_week FROM teachers''')
    teacherList = cur.fetchall()
    cur.close()
    return teacherList


if __name__ == '__main__':
    app.run()
