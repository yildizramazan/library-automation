# after running "pip install -r requirements.txt" on terminal

import pyodbc  # library for connecting to databases using odbc
from flask import Flask, render_template, redirect, url_for, flash  # flask modules for web development
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash  # modules for password hashing
from flask_wtf import FlaskForm  # module for creating web forms
from wtforms import StringField, IntegerField, PasswordField, SubmitField  # fields for the forms
from wtforms.validators import DataRequired  # validator to ensure required fields are not empty

# create a flask application
app = Flask(__name__)

# set a secret key for session management and csrf protection
app.secret_key = "database-library-automation-project-240709022"

# define database connection details
server = 'localhost'  # database server address
database = 'library_db'  # name of the database
server_username = 'SA'  # database username
server_password = 'LibraryAutomation220709024'  # database password

# establish a connection to the sql server database using pyodbc
conn = pyodbc.connect(
    f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={server_username};PWD={server_password};TrustServerCertificate=yes;',
    autocommit=True  # enable autocommit to apply changes immediately. not needing to use conn.commit().
)

# store the database connection in flask app configuration
app.config['DB_CONNECTION'] = conn

# create a cursor object to execute sql queries
cursor = conn.cursor()

# initialize flask-login for managing user sessions
login_manager = LoginManager()
login_manager.init_app(app)  # bind flask-login to the flask app
login_manager.login_view = 'login'  # set the default login view

# define a user model that inherits from flask login's UserMixin
class User(UserMixin):
    def __init__(self, id, name, email, role):
        self.id = id  # unique identifier for the user
        self.name = name  # full name of the user
        self.email = email  # email address of the user
        self.role = role  # role of the user (admin or standard user)

    # method to check if the user has an admin role
    def is_admin(self):
        return self.role == "Admin"  # return true if the user is an admin

# function to load user information from the database using flask-login
@login_manager.user_loader
def load_user(user_id):
    # execute a query to retrieve user details by user id
    cursor.execute("SELECT KullaniciID, AdSoyad, Eposta, Rol FROM Kullanicilar WHERE KullaniciID = ?", user_id)
    user = cursor.fetchone()  # fetch the result of the query

    # if a user is found, return a User object
    if user:
        return User(id=user.KullaniciID, name=user.AdSoyad, email=user.Eposta, role=user.Rol)

    # return none if no user is found
    return None

# form class for adding a new book to the library database
class AddBookForm(FlaskForm):
    baslik = StringField('Book Name', validators=[DataRequired()])  # field for book title
    yazar = StringField('Author', validators=[DataRequired()])  # field for author's name
    yayinevi = StringField('Publisher', validators=[DataRequired()])  # field for publisher name
    isbn = IntegerField('ISBN', validators=[DataRequired()])  # field for isbn
    tur = StringField('Genre', validators=[DataRequired()])  # field for book genre
    submit = SubmitField('Add Book')  # submit button for the form

# form class for editing an existing book in the database
class EditBookForm(FlaskForm):
    baslik = StringField('Book Name', validators=[DataRequired()])  # field for book title
    yazar = StringField('Author', validators=[DataRequired()])  # field for author's name
    yayinevi = StringField('Publisher', validators=[DataRequired()])  # field for publisher name
    isbn = IntegerField('ISBN', validators=[DataRequired()])  # field for isbn
    tur = StringField('Genre', validators=[DataRequired()])  # field for book genre
    submit = SubmitField('Edit Book')  # submit button for the form

# form class for searching books in the library
class SearchForm(FlaskForm):
    search_bar = StringField('Search Bar', validators=[DataRequired()])  # input field for search queries
    submit = SubmitField('Search')  # submit button for the form

# form class for user registration
class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])  # field for user's first name
    surname = StringField('Surname', validators=[DataRequired()])  # field for user's last name
    username = StringField('Username', validators=[DataRequired()])  # field for desired username
    password = PasswordField('Password', validators=[DataRequired()])  # field for password
    submit = SubmitField('Register')  # submit button for the form

# form class for user login
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])  # field for username
    password = PasswordField('Password', validators=[DataRequired()])  # field for password
    submit = SubmitField('Login')


# function to add a new book using a stored procedure
def add_book(baslik, yazar, yayinevi, isbn, tur):
    # call the stored procedure Book_Add with the provided parameters
    cursor.execute(
            "EXEC Book_Add @Baslik = ?, @Yazar = ?, @Yayinevi = ?, @ISBN = ?, @Tur = ?",
            (baslik, yazar, yayinevi, isbn, tur)
        )

# route for the home page
@app.route('/', methods=["GET", "POST"])
def index():
    results = []  # list to store search results
    is_admin = False  # boolean to track if the current user is an admin

    # check if the user is logged in
    if current_user.is_authenticated:
        is_admin = current_user.is_admin()  # check if the user is admin
        loggedin = True  # boolean to track if a user has logged in
    else:
        loggedin = False

    # create an instance of the search form
    searchform = SearchForm()
    if searchform.validate_on_submit():  # check if the form submission is valid
        query = f"%{searchform.search_bar.data}%"  # prepare the search query
        # call the stored procedure Book_Search to search for books
        cursor.execute(
            """
            EXEC Book_Search @SearchTerm = ?
            """,
            query
        )
        # fetch all results returned by the query
        results = cursor.fetchall()
    # render the index.html template with the search results and user information
    return render_template('index.html', results=results, searchform=searchform, is_admin=is_admin, loggedin=loggedin)

# route for the users account page (accessible only if logged in and also not available for admin because it has an admin panel)
@app.route('/account')
@login_required  # ensure the user is logged in before accessing this route
def account():
    # restrict access to non-admin users only
    if current_user.is_admin():
        return redirect(url_for('index'))  # redirect to the home page

    kullanıcıid = current_user.id  # get the current users id
    name = current_user.name  # get the current users name
    role = current_user.role  # get the current users role

    # query the total number of books borrowed by the user using a scalar function called GetUserBorrowedBooksCount
    cursor.execute("SELECT dbo.GetUserBorrowedBooksCount(?) AS BookCount", kullanıcıid)
    book_count = cursor.fetchone().BookCount  # retrieve the count from the query result

    # query to fetch the user's borrowing history and related book details
    query = """
        SELECT OduncIslemleri.IslemID, Kitaplar.KitapID, Kitaplar.Baslik, Kitaplar.Yazar, 
               OduncIslemleri.OduncTarihi, OduncIslemleri.SonTeslimTarihi, OduncIslemleri.TeslimTarihi, OduncIslemleri.Durum
        FROM OduncIslemleri
        JOIN Kitaplar ON OduncIslemleri.KitapID = Kitaplar.KitapID
        WHERE OduncIslemleri.KullaniciID = ?
    """
    cursor.execute(query, kullanıcıid)  # execute the query with the user's id
    books = cursor.fetchall()  # fetch all rows from the query result

    # render the dashboard.html template with the user's data and borrowing history
    return render_template("dashboard.html", name=name, role=role, books=books, book_count=book_count)

# route fır the user to return a borrowed book. this <int:id> receives the id that comes from url_for link
@app.route('/return-book/<int:id>')
def return_book(id): # <int:id> = id
    # gets the current user's id
    kullanıcıid = current_user.id
    # updates the borrowing record to mark the book as returned
    cursor.execute(
        """
        UPDATE OduncIslemleri
        SET TeslimTarihi = GETDATE(), Durum = 'IadeEdildi'
        WHERE KullaniciID = ? AND KitapID = ? AND TeslimTarihi IS NULL
        """,
        (kullanıcıid, id) # <int:id> = id
    )
    # updates the book's status to available
    cursor.execute("UPDATE Kitaplar SET Durum = 'Mevcut' WHERE KitapID = ?", id)
    # redirects to the account page after returning the book
    return redirect(url_for('account'))

# route for the admin panel
@app.route('/admin')
@login_required
def admin_panel():
    # checks if the user is not an admin. if is admin then the user can access the admin panel
    if not current_user.is_admin():
        # redirects to the home page
        return redirect(url_for('index'))
    # renders the admin panel page
    return render_template('admin.html')


# a route for admin to see all the books listed
@app.route('/all-books-listed')
@login_required
def all_books_listed():
    # checks if the user is not an admin
    if not current_user.is_admin():
        # redirects to the home page
        return redirect(url_for('index'))
    # selects all books from the database
    cursor.execute("SELECT * FROM Kitaplar")
    books = cursor.fetchall()
    # fetches the count of available books with a sql function
    cursor.execute("SELECT dbo.GetAvailableBooksCount() AS AvailableBooks")
    available_books_count = cursor.fetchone().AvailableBooks
    # renders the page with data
    return render_template('all-books.html', books=books, available_books_count=available_books_count)

# the route for user to see the logs (edit, delete, insert procedures)
@app.route('/book-logs')
@login_required
def logs():
    # checks if the user is not an admin because it is only available for the admin
    if not current_user.is_admin():
        return redirect(url_for('index'))
    # updates book log to mark deleted items
    cursor.execute("UPDATE Kitaplog SET Islem = 'Silindi' WHERE KitapID = NULL")
    # selects logs with formatted dates
    cursor.execute("SELECT CONVERT(NVARCHAR, Tarih, 3) AS Tarih, Baslik, Islem FROM KitapLog")
    all_logs = cursor.fetchall()
    # renders the logs page
    return render_template('logs.html', logs=all_logs)


# the route that has the add form for the admin to add a book
@app.route('/add', methods=['GET', 'POST'])
def add():
    # checks if the user is not an admin
    if not current_user.is_admin():
        return redirect(url_for('index'))
    # creates an instance of the add book form
    add_form = AddBookForm()
    # handles form submission
    if add_form.validate_on_submit():
        # calls the add_book function with form data
        add_book(baslik=add_form.baslik.data,
                 yazar=add_form.yazar.data,
                 yayinevi=add_form.yayinevi.data,
                 isbn=add_form.isbn.data,
                 tur=add_form.tur.data
                 )
        # redirects to the home page
        return redirect(url_for("index"))
    # renders the add book page with the form
    return render_template('add.html', form=add_form)


# a route for admin to delete books. it does not render a html file only deletes and redirects to the all_books_listed page
@app.route('/delete/<int:id>')
@login_required
def delete_book(id):
    # checks if the user is not an admin
    if not current_user.is_admin():
        return redirect(url_for('index'))

    cursor.execute("EXEC Book_Delete @KitapID = ?", id)
    return redirect(url_for('all_books_listed'))


# a route that is for the user to borrow a book. again it doesn't render a html file but only works like a function
@app.route('/borrow/<int:kitapid>')
@login_required
def borrow_book(kitapid):
    # fetches the current status of the book
    cursor.execute("SELECT Durum FROM Kitaplar WHERE KitapID = ?", kitapid)
    kitap_durum = cursor.fetchone()[0]
    # checks if the book is available
    if kitap_durum == "Mevcut":
        # inserts a borrowing record for the user
        cursor.execute(
            """
            INSERT INTO OduncIslemleri (KullaniciID, KitapID, OduncTarihi, SonTeslimTarihi, TeslimTarihi)
            VALUES (?, ?, GETDATE(), DATEADD(DAY, 15, GETDATE()), NULL)
            """,
            (current_user.id, kitapid)
        )
        # updates the book status to borrowed
        cursor.execute(
            "UPDATE Kitaplar SET Durum = 'OduncAlindi' WHERE KitapID = ?",
            kitapid
        )
    return redirect(url_for('index'))

# the route that has the register form for a new user to register
@app.route('/register', methods=['GET', 'POST'])
def register():
    # creates an instance of the register form
    register_form = RegisterForm()
    # handles the submission
    if register_form.validate_on_submit():
        # retrieves form data for a new user
        new_name = register_form.name.data
        new_surname = register_form.surname.data
        new_username = register_form.username.data
        new_password = generate_password_hash(register_form.password.data)  # hashes the password for extra security
        # checks if the username already exists
        cursor.execute("SELECT * FROM Kullanicilar WHERE Eposta = ?", new_username)
        user = cursor.fetchone()
        if user:
            # it redirects to the register page if the username is taken
            return redirect(url_for('register'))

        # inserts a new user into the database
        cursor.execute(
            "EXEC User_Add @AdSoyad = ?, @Eposta = ?, @Sifre = ?, @Rol = ?",
            (f"{new_name} {new_surname}", new_username, new_password, "Kullanici")
        )
        return redirect(url_for('login'))

    # renders the registration page with the form
    return render_template('register.html', form=register_form)



# the route that has the login form for a user to login
@app.route('/login', methods=['GET', 'POST'])
def login():
    # creates an instance of the login form
    login_form = LoginForm()
    if login_form.validate_on_submit():
        # retrieves the username and password from the form
        username = login_form.username.data
        password = login_form.password.data

        # queries the database for the user
        cursor.execute("SELECT KullaniciID, AdSoyad, Eposta, Sifre, Rol FROM Kullanicilar WHERE Eposta = ?", username)
        user = cursor.fetchone()

        if user:
            # checks if the password matches the stored hash
            if check_password_hash(user.Sifre, password):
                # creates a user object for flask-login
                user_obj = User(id=user.KullaniciID, name=user.AdSoyad, email=user.Eposta, role=user.Rol)
                login_user(user_obj)  # logs in the user
                return redirect(url_for('index'))
            else:
                # flashes an error for incorrect password
                print("incorrect password! please try again.")
                flash("incorrect password! please try again.", "danger")
        else:
            # if there is no user that has the entered username, redirects again to the login page to delete the username from the form
            return redirect(url_for('login'))

    # renders the login page with the form
    return render_template('login.html', form=login_form)

# a route that basically logs out the user
@app.route('/logout')
@login_required
def logout():
    # logs out the current user
    logout_user()
    # redirects to the login page
    return redirect(url_for('login'))

# this route shows the book with edit and delete buttons if the user is admin but shows the borrow book button if the user is a standard user
@app.route('/show-book/<int:id>')
def show_individual(id):
    # checks if the user is authenticated and checks the role and sets flags
    is_admin = False
    if current_user.is_authenticated:
        is_admin = current_user.is_admin()
        loggedin = True
    else:
        loggedin = False
    # queries the database for the book details
    cursor.execute("SELECT * FROM Kitaplar WHERE KitapID = ?", id)
    book = cursor.fetchone()
    # determines if the book is available
    if book.Durum == 'OduncAlindi':
        available = False
    else:
        available = True
    # renders the book details page
    return render_template("book.html", book=book, user=current_user, is_admin=is_admin, loggedin=loggedin, available=available)

# the route that has the edit form for the admin to edit a specific book
@app.route('/edit-book/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    # checks if the user is not an admin
    if not current_user.is_admin():
        # redirects to the home page
        return redirect(url_for('index'))

    # creates an instance of the edit book form
    edit_form = EditBookForm()
    # fetches the current details of the book
    cursor.execute("SELECT * FROM Kitaplar WHERE KitapID = ?", id)
    book = cursor.fetchone()

    # pre-fills the form with the current book details
    edit_form.baslik.data = book.Baslik
    edit_form.yazar.data = book.Yazar
    edit_form.yayinevi.data = book.Yayinevi
    edit_form.isbn.data = book.ISBN
    edit_form.tur.data = book.Tur

    if edit_form.validate_on_submit():
        # retrieves updated book details from the form
        yeni_baslik = edit_form.baslik.data
        yeni_yazar = edit_form.yazar.data
        yeni_yayınevi = edit_form.yayinevi.data
        yeni_isbn = edit_form.isbn.data
        yeni_tur = edit_form.tur.data

        # calls the stored procedure to update the book details
        cursor.execute(
            """
            EXEC Book_Update @KitapID = ?, @Baslik = ?, @Yazar = ?, @Yayinevi = ?, @ISBN = ?, @Tur = ?
            """,
            (id, yeni_baslik, yeni_yazar, yeni_yayınevi, yeni_isbn, yeni_tur)
        )

        # redirects to the book details page
        return redirect(url_for('show_individual', id=id))

    # renders the edit book page with the form
    return render_template('edit.html', edit_form=edit_form, id=id)

# a route that shows a list of all the users and their current book counts
@app.route('/active-users')
def get_active_users():
    # calls the sql function to get active users
    cursor.execute("SELECT * FROM GetActiveUsers() ORDER BY ToplamOduncSayisi DESC;")
    rows = cursor.fetchall()  # fetches the results
    # renders the active users page
    return render_template('active-users.html', rows=rows)

# a route that shows the books with the amount of how many times they were taken by a user
@app.route('/popular-books')
@login_required
def popular_books():
    # queries the popular books table
    cursor.execute("SELECT * FROM PopulerKitaplar ORDER BY OduncSayisi DESC;")
    books = cursor.fetchall()  # fetches the results
    # renders the popular books page
    return render_template("popular-books.html", books=books)



if __name__ == '__main__':
    app.run(debug=True, port=5004) # starts the flask application


# closes the cursor to release database resources
cursor.close()
# closes the database connection
conn.close()