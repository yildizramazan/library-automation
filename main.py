import pyodbc
from flask import Flask, render_template, redirect, url_for, request, flash, session, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField
from wtforms.validators import DataRequired


app = Flask(__name__)
app.secret_key = "database-library-automation-project-240709022"

server = 'localhost'
database = 'master'
server_username = 'SA'
server_password = 'YourPassword123'
conn = pyodbc.connect(
    f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={server_username};PWD={server_password};TrustServerCertificate=yes;',
    autocommit=True
)

cursor = conn.cursor()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, name, email, role):
        self.id = id
        self.name = name
        self.email = email
        self.role = role

    def is_admin(self):
        return self.role == "Admin"


@login_manager.user_loader
def load_user(user_id):
    # Kullanıcıyı veritabanından çek
    cursor.execute("SELECT KullaniciID, AdSoyad, Eposta, Rol FROM Kullanıcılar WHERE KullaniciID = ?", user_id)
    user = cursor.fetchone()
    if user:
        return User(id=user.KullaniciID, name=user.AdSoyad, email=user.Eposta, role=user.Rol)
    return None


class AddBookForm(FlaskForm):
    baslik = StringField('Book Name', validators=[DataRequired()])
    yazar = StringField('Author', validators=[DataRequired()])
    yayinevi = StringField('Publisher', validators=[DataRequired()])
    isbn = IntegerField('ISBN', validators=[DataRequired()])
    tur = StringField('Genre', validators=[DataRequired()])
    submit = SubmitField('Add Book')



class EditBookForm(FlaskForm):
    baslik = StringField('Book Name', validators=[DataRequired()])
    yazar = StringField('Author', validators=[DataRequired()])
    yayinevi = StringField('Publisher', validators=[DataRequired()])
    isbn = IntegerField('ISBN', validators=[DataRequired()])
    tur = StringField('Genre', validators=[DataRequired()])
    submit = SubmitField('Edit Book')


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


def add_book(baslik, yazar, yayinevi, isbn, tur):
    cursor.execute(
        "INSERT INTO Kitaplar (Baslik, Yazar, Yayinevi, ISBN, Tur) VALUES (?, ?, ?, ?, ?)",
        (baslik, yazar, yayinevi, isbn, tur)
    )




@app.route('/', methods=["GET", "POST"])
def index():
    results = []
    is_admin = False
    if current_user.is_authenticated:
        is_admin = current_user.is_admin()
        loggedin = True
    else:
        loggedin = False

    searchform = SearchForm()
    if searchform.validate_on_submit():
        query = f"%{searchform.search_bar.data}%"
        cursor.execute("SELECT * FROM Kitaplar WHERE "
                       "Baslik LIKE (?) OR Yazar LIKE (?) OR Yayinevi LIKE (?) OR Baslik LIKE (?) OR ISBN LIKE (?)",
                       (query, query, query, query, query)
        )
        results = cursor.fetchall()
    return render_template('index.html', results=results, searchform=searchform, is_admin=is_admin, loggedin=loggedin)



@app.route('/account')
@login_required  # Kullanıcının giriş yapması zorunlu
def account():
    if current_user.is_admin():
        print("Bu sayfaya erişim yetkiniz yok!")
        flash("Bu sayfaya erişim yetkiniz yok!", "danger")
        return redirect(url_for('index'))
    kullanıcıid = current_user.id
    name = current_user.name
    role = current_user.role
    cursor.execute("SELECT * FROM OduncIslemleri WHERE KullaniciID = ?", kullanıcıid)
    books = cursor.fetchall()
    return render_template("dashboard.html", name=name, role=role, books=books)


@app.route('/return-book/<int:id>')
def return_book(id):
    print(id, current_user.id)
    kullanıcıid = current_user.id
    cursor.execute("DELETE FROM OduncIslemleri WHERE KullaniciID = ? AND KitapID = ?", (kullanıcıid, id))
    conn.commit()
    cursor.execute("UPDATE Kitaplar SET Durum = 'Mevcut' WHERE KitapID = ?", id)
    conn.commit()
    return redirect(url_for('account'))



@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin():
        print("Bu sayfaya erişim yetkiniz yok!")
        flash("Bu sayfaya erişim yetkiniz yok!", "danger")
        return redirect(url_for('index'))
    return render_template('admin.html')


@app.route('/add', methods=['GET', 'POST'])
def add():
    if not current_user.is_admin():
        print("Bu sayfaya erişim yetkiniz yok!")
        flash("Bu sayfaya erişim yetkiniz yok!", "danger")
        return redirect(url_for('index'))
    add_form = AddBookForm()
    if add_form.validate_on_submit():
        print(add_form.baslik.data, add_form.yazar.data ,add_form.yayinevi.data, add_form.isbn.data)
        add_book(baslik=add_form.baslik.data, yazar=add_form.yazar.data, yayinevi=add_form.yayinevi.data, isbn=add_form.isbn.data, tur=add_form.tur.data)
        return redirect(url_for("index"))
    return render_template('add.html', form=add_form)



@app.route('/delete/<int:id>')
@login_required
def delete_book(id):
    if not current_user.is_admin():
        print("bu silme işlemini yapma yetkiniz yok")
        flash("Bu sayfaya erişim yetkiniz yok!", "danger")
        return redirect(url_for('index'))
    try:
        # Kitabı veritabanından sil
        cursor.execute("DELETE FROM Kitaplar WHERE KitapID = ?", id)
        conn.commit()
        flash('Kitap başarıyla silindi!', 'success')
    except Exception as e:
        flash(f'Hata: {e}', 'danger')

    # Silme işleminden sonra liste sayfasına yönlendir
    return redirect(url_for('index'))



@app.route('/borrow/<int:kitapid>')
@login_required
def borrow_book(kitapid):
    try:
        cursor.execute("SELECT Durum FROM Kitaplar WHERE KitapID = ?", kitapid)
        kitap_durum = cursor.fetchone()[0]
        print(kitap_durum)
        if kitap_durum == "Mevcut":
            cursor.execute("INSERT INTO OduncIslemleri (KullaniciID, KitapID, OduncTarihi, TeslimTarihi)"
                            "VALUES (?, ?, GETDATE(), DATEADD(DAY, 15, GETDATE()))",
                           (current_user.id, kitapid) )
            conn.commit()
            cursor.execute(
                "UPDATE Kitaplar SET Durum = 'OduncAlindi' WHERE KitapID = ?",
                kitapid
            )
            conn.commit()
        else:
            print("kitap ödünç alınmadı çünkü ödünç alınmış")
            flash('Hata: Kitap ödünç alınmış', 'danger')

    except Exception as e:
        print("kitap ödünç alınmadı 2")
        flash(f'Hata: {e}', 'danger')
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        new_name = register_form.name.data
        new_surname = register_form.surname.data
        new_username = register_form.username.data
        new_password = generate_password_hash(register_form.password.data)
        print(new_password)
        # Kullanıcı adı kontrolü
        cursor.execute("SELECT * FROM Kullanıcılar WHERE Eposta = ?", new_username)
        print(new_username)
        user = cursor.fetchone()
        if user:
            flash("Bu kullanıcı adı zaten alınmış!", "danger")
            return redirect(url_for('register'))

        # Yeni kullanıcı ekleme
        cursor.execute(
            "INSERT INTO Kullanıcılar (AdSoyad, Eposta, Sifre, Rol) VALUES (?, ?, ?, ?)",
            (f"{new_name} {new_surname}", new_username, new_password, "Kullanici")
        )
        conn.commit()
        flash("Kayıt başarılı! Şimdi giriş yapabilirsiniz.", "success")
        return redirect(url_for('login'))

    return render_template('register.html', form=register_form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        username = login_form.username.data
        password = login_form.password.data

        # Kullanıcıyı veritabanından kontrol et
        cursor.execute("SELECT KullaniciID, AdSoyad, Eposta, Sifre, Rol FROM Kullanıcılar WHERE Eposta = ?", username)
        user = cursor.fetchone()

        if user:
            # Veritabanından dönen şifreyi kontrol et
            if check_password_hash(user.Sifre, password):
                user_obj = User(id=user.KullaniciID, name=user.AdSoyad, email=user.Eposta, role=user.Rol)
                login_user(user_obj)  # Flask-Login ile kullanıcıyı oturum açtır
                print(f"Hoşgeldiniz, {user.AdSoyad}!")
                flash(f"Hoşgeldiniz, {user.AdSoyad}!", "success")
                return redirect(url_for('index'))  # Ana sayfaya yönlendir
            else:
                print("Hatalı şifre! Lütfen tekrar deneyin.")
                flash("Hatalı şifre! Lütfen tekrar deneyin.", "danger")
        else:
            print("Böyle bir kullanıcı bulunamadı!")
            flash("Böyle bir kullanıcı bulunamadı!", "danger")

    return render_template('login.html', form=login_form)  # Login formu sayfasını render et

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Başarıyla çıkış yaptınız!", "success")
    return redirect(url_for('login'))

@app.route('/show-book/<int:id>')
def show_individual(id):

    is_admin = False
    if current_user.is_authenticated:
        is_admin = current_user.is_admin()
        loggedin = True
    else:
        loggedin = False
    cursor.execute("SELECT * FROM Kitaplar WHERE KitapID = ?", id)
    book = cursor.fetchone()
    if book.Durum == 'OduncAlindi':
        available = False
    else:
        available = True
    return render_template("book.html", book=book, user=current_user, is_admin=is_admin, loggedin=loggedin, available=available)


@app.route('/edit-book/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    if not current_user.is_admin():
        print("Bu sayfaya erişim yetkiniz yok!")
        flash("Bu sayfaya erişim yetkiniz yok!", "danger")
        return redirect(url_for('index'))
    edit_form = EditBookForm()
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
        return redirect(url_for('show_individual', id=id))

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
