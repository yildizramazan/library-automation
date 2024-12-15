from idlelib.query import Query

import pyodbc
from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from  flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.secret_key = "database-library-automation-project-240709022"
Bootstrap(app)

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
    tur = StringField('Tür', validators=[DataRequired()])
    submit = SubmitField('Add Book')



class SearchForm(FlaskForm):
    search_bar = StringField('Search Bar', validators=[DataRequired()])
    submit = SubmitField('Search')

class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


cursor = conn.cursor()

def add_book(baslik, yazar, yayinevi, isbn, tur):
    cursor.execute(
        "INSERT INTO Kitaplar (Baslik, Yazar, Yayinevi, ISBN, Tur) VALUES (?, ?, ?, ?, ?)",
        (baslik, yazar, yayinevi, isbn, tur)
    )


@app.route('/', methods=["GET", "POST"])
def index():
    results = []
    query = ""
    searchform = SearchForm()
    if searchform.validate_on_submit():
        query = f"%{searchform.search_bar.data}%"
        cursor.execute("SELECT * FROM Kitaplar WHERE "
                       "Baslik LIKE (?) OR Yazar LIKE (?) OR Yayinevi LIKE (?) OR Baslik LIKE (?) OR ISBN LIKE (?)",
                       (query, query, query, query, query)
        )
        results = cursor.fetchall()
    return render_template('index.html', results=results, searchform=searchform)


@app.route('/add', methods=['GET', 'POST'])
def add():
    add_form = AddBookForm()
    if add_form.validate_on_submit():
        print(add_form.baslik.data, add_form.yazar.data ,add_form.yayinevi.data, add_form.isbn.data)
        add_book(baslik=add_form.baslik.data, yazar=add_form.yazar.data, yayinevi=add_form.yayinevi.data, isbn=add_form.isbn.data, tur=add_form.tur.data)
        return redirect(url_for("index"))
    return render_template('add.html', form=add_form)



@app.route('/delete/<int:id>')
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




@app.route('/show-book/<int:id>')
def show_individual(id):
    cursor.execute("SELECT * FROM Kitaplar WHERE KitapID = ?", id)
    book = cursor.fetchone()
    return render_template("book.html", book=book)


# @app.route('/edit-book/<int:id>', methods=['GET', 'POST'])
# def edit_book(id):
#     edit_form = AddBookForm()
#     if edit_form.validate_on_submit():
#         yeni_baslik = edit_form.baslik.data
#         yeni_yazar = edit_form.yazar.data
#         yeni_yayınevi = edit_form.yayinevi.data
#         yeni_isbn = edit_form.isbn.data
#         yeni_tur = edit_form.tur.data
#         cursor.execute("UPDATE Kitaplar SET Baslik = ?, Yazar = ?, Yayınevi = ?, ISBN = ? ,Tur = ? WHERE KitapID = ?", (yeni_baslik, yeni_yazar, yeni_yayınevi, yeni_isbn, yeni_tur, id ))
#     return render_template('edit.html', edit_form=edit_form)
#
#

@app.route('/edit-book/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    edit_form = AddBookForm()
    if edit_form.validate_on_submit():
        yeni_baslik = edit_form.baslik.data
        yeni_yazar = edit_form.yazar.data
        yeni_yayınevi = edit_form.yayinevi.data
        yeni_isbn = edit_form.isbn.data
        yeni_tur = edit_form.tur.data

        cursor.execute(
            "UPDATE Kitaplar SET Baslik = ?, Yazar = ?, Yayinevi = ?, ISBN = ?, Tur = ? WHERE KitapID = ?",
            (yeni_baslik, yeni_yazar, yeni_yayınevi, yeni_isbn, yeni_tur, id)
        )
        conn.commit()
        flash('Kitap başarıyla güncellendi!', 'success')
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM Kitaplar WHERE KitapID = ?", id)
    book = cursor.fetchone()

    edit_form.baslik.data = book.Baslik
    edit_form.yazar.data = book.Yazar
    edit_form.yayinevi.data = book.Yayinevi
    edit_form.isbn.data = book.ISBN
    edit_form.tur.data = book.Tur
    
    return render_template('edit.html', edit_form=edit_form, id=id)


if __name__ == '__main__':
    app.run(debug=True, port=5002)

cursor.close()
conn.close()
