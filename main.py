import pyodbc
from flask import Flask, render_template
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

server = 'localhost'
database = 'master'
username = 'SA'
password = 'YourPassword123'
conn = pyodbc.connect(
    f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;',
    autocommit=True
)

cursor = conn.cursor()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login')
def login():
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True, port=5001)

cursor.close()
conn.close()
