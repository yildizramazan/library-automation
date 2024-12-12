import pyodbc
from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from  flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.secret_key = "database-library-automation-project-240709022"

server = 'localhost'
database = 'master'
username = 'SA'
password = 'YourPassword123'
conn = pyodbc.connect(
    f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;',
    autocommit=True
)

class AddBookForm(FlaskForm):
    baslik = StringField('Kitap Adı', validators=[DataRequired()])
    yazar = StringField('Yazar', validators=[DataRequired()])
    yayinevi = StringField('Yayınevi', validators=[DataRequired()])
    isbn = IntegerField('ISBN', validators=[DataRequired()])
    submit = SubmitField('Add Book')

cursor = conn.cursor()

def add_book(baslik, yazar, yayinevi, isbn):
    cursor.execute(
        "INSERT INTO Kitaplar (Baslik, Yazar, Yayinevi, ISBN) VALUES (?, ?, ?, ?)",
        (baslik, yazar, yayinevi, isbn)
    )



@app.route('/')
def index():
    cursor.execute("SELECT * FROM Kitaplar")
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row.KitapID}, Başlık: {row.Baslik}, Yazar: {row.Yazar}, Yayınevi: {row.Yayinevi}, ISBN: {row.ISBN}, Durum: {row.Durum}")

    return render_template("index.html", rows=rows)


@app.route('/add', methods=['GET', 'POST'])
def add():
    add_form = AddBookForm()
    if add_form.validate_on_submit():
        print(add_form.baslik.data, add_form.yazar.data ,add_form.yayinevi.data, add_form.isbn.data)
        add_book(baslik=add_form.baslik.data, yazar=add_form.yazar.data, yayinevi=add_form.yayinevi.data, isbn=add_form.isbn.data)
        return redirect(url_for("index"))
    return render_template('add.html', form=add_form)


@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_book(id):
    try:
        # Kitabı veritabanından sil
        cursor.execute("DELETE FROM Kitaplar WHERE KitapID = ?", id)
        conn.commit()
        flash('Kitap başarıyla silindi!', 'success')
    except Exception as e:
        flash(f'Hata: {e}', 'danger')

    # Silme işleminden sonra liste sayfasına yönlendir
    return redirect(url_for('index'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/show-book/<id>')
def show_individual(id):
    cursor.execute(f"SELECT * FROM Kitaplar WHERE KitapID = {id}")
    book = cursor.fetchone()
    return render_template("book.html", book=book)



if __name__ == '__main__':
    app.run(debug=True, port=5002)

cursor.close()
conn.close()
