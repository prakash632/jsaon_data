from flask import Flask, render_template, request, redirect, url_for, session,flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory
import pandas as pd
import json
import pymysql
import mysql.connector as i
#from mysql import connector
from pandas.io import sql
ALLOWED_EXTENSIONS = set(['json'])


app = Flask(__name__, template_folder='template')


UPLOAD_FOLDER = 'F:/files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456789'
app.config['MYSQL_DB'] = 'flask_project'


mysql = MySQL(app)

@app.route('/pythonlogin/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:

        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()

        if account:

            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('index.html', msg='')

@app.route('/pythonlogin/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    msg = ''

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:

        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('register.html', msg=msg)


@app.route('/pythonlogin/home')
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])

    return redirect(url_for('login'))

@app.route('/pythonlogin/profile')
def profile():

    if 'loggedin' in session:

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()

        return render_template('profile.html', account=account)

    return redirect(url_for('login'))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':

        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            k = filename
            pa = 'F:/files/' + filename

            f = open(pa)

            data = json.load(f)
            dff = pd.read_json(pa)
            username = session['username']

            curso = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            curso.execute('INSERT INTO files VALUES (NULL, %s, %s)', (username, k,))

            mysql.connection.commit()
            mydb = pymysql.connect(host="localhost",
                                   user="root",
                                   password="123456789",
                                   database="flask_project")

            dff.to_sql(con=mydb,name='data', if_exists = 'replace', index=False)
            mydb.commit()

            return redirect(url_for('uploaded_file',
                                    filename=filename))

    return render_template('upload.html')



@app.route('/uploads/<filename>')
def uploaded_file(filename):
    path = "F:/files/" + filename
    df1 = pd.read_json(path)
    return render_template('df.html', data=df1.to_html())

@app.route('/display', methods=['GET', 'POST'])
def display_file():
    if request.method == 'GET':

        username = session['username']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT f_username as Username,file_path as FileName FROM files WHERE f_username = %s', (username,))
        df = pd.DataFrame(cursor.fetchall())

        return render_template('display.html',  tables=[df.to_html(classes='data', header="true")])

@app.route('/view', methods=['GET', 'POST'])
def view_file():
    if request.method == 'GET':

        username = session['username']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM data')
        df = pd.DataFrame(cursor.fetchall())
        return render_template('view.html',  tables=[df.to_html(classes='data', header="true")])
if __name__ == '__main__':
    app.run(debug = True)