# Library Automation

## Project Description

Library Automation is a web-based system designed to manage and streamline the process of borrowing and returning books in a library. This project provides an efficient and user-friendly interface for both library administrators and users to perform various library-related operations.

## Features

- User authentication and role-based access (e.g., Admin and User roles).
- Manage library resources (add, edit, delete books).
- Borrow and return books functionality.
- Search for books using filters.
- Interactive and responsive web interface built using Jinja templating with HTML.

---

## Technologies Used

- **Backend:** Python (Flask framework)
- **Frontend:** HTML with Jinja2 templates
- **Database:** Microsoft SQL Server
- **Additional Libraries:**
  - pyodbc
  - Flask-Login
  - Flask-WTF
  - WTForms
  - Werkzeug

---

## Setup Instructions

### For Windows Users:

1. Restore the database named `library_db`. Microsoft SQL Server Studio.

2. Install necessary libraries by running:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure the database connection in `main.py`:
   ```python
   connection_string = (
       "Driver={ODBC Driver 17 for SQL Server};"
       "Server=HP-OMEN15;"  # Replace with your server name
       "Database=library_db;"  # Replace with your database name
       "Trusted_Connection=yes;"
   )
   conn = pyodbc.connect(connection_string)
   ```

### For macOS Users (Using Azure Data Studio and Docker Container):

1. Install Docker and Azure Data Studio.
2. Pull the Microsoft SQL Server image by running:
   ```bash
   docker pull mcr.microsoft.com/mssql/server:latest
   ```
3. Create and run a SQL Server container using the following command:
   ```bash
   docker run -e 'ACCEPT_EULA=Y' -e 'MSSQL_SA_PASSWORD=LibraryAutomation220709024' -p 1433:1433 --name sql_server_container -d mcr.microsoft.com/mssql/server
   ```
4. Open Azure Data Studio.
5. Select **Connection Type** as `Microsoft SQL Server` and enter the following details:
   - **Server:** `localhost`
   - **Authentication Type:** `SQL Login`
   - **Username:** `SA`
   - **Password:** `LibraryAutomation220709024`
   - **Trust Server Certificate:** Set to `True`.
6. Click **Connect** to establish a connection to the database.

7. Once connected, restore the database named `library_db`.
8. Install necessary Python libraries by running:
   ```bash
   pip install -r requirements.txt
   ```
9. Configure the database connection in Python in `main.py`:
   ```python
   server = 'localhost'  # Database server address
   database = 'library_db'  # Database name
   server_username = 'SA'
   server_password = 'LibraryAutomation220709024' 

   conn = pyodbc.connect(
       f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={server_username};PWD={server_password};TrustServerCertificate=yes;',
       autocommit=True
   )
   ```

---

## How to Run the Application


1. Start the Flask server by running the following command in the project directory or just by clicking the run button:
   ```bash
   python3 main.py
   ```
2. Access the application in your browser at `http://127.0.0.1:5000/`.

---

## Project Information
- **Developer:** Ramazan Yıldız
- **Student ID:** 220709024
- **Course Name:** Database Management Systems
- **Database:** Microsoft SQL Server

