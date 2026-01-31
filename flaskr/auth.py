import sqlite3
import bcrypt
import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

        try:
            self.conn = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
            self.cursor = self.conn.cursor()

            # Enable WAL mode (persistent)
            self.cursor.execute("PRAGMA journal_mode=WAL;")
            
            self.cursor.execute("PRAGMA synchronous=NORMAL;")
            self.cursor.execute("PRAGMA foreign_keys=ON;")

            self.conn.execute("PRAGMA busy_timeout=30000;")  # 30 seconds

        except sqlite3.Error as e:
            print(f"Error connecting to auth database: {e}\nExiting...")
            exit(1)

    def close(self):
        self.conn.close()

    def verifyTables(self):
        # Verify and create tables if they do not exist
        table_creation_queries = {
            "user": """
                CREATE TABLE IF NOT EXISTS users (
                    userID INTEGER PRIMARY KEY,
                    username TEXT NOT NULL CHECK (length(username) <= 40),
                    password_hash TEXT NOT NULL,
                    email TEXT NOT NULL CHECK (length(email) <= 100),
                    UNIQUE (username),
                    UNIQUE (email)
                );
            """
        }

        for table_name, query in table_creation_queries.items():
            try:
                self.cursor.execute(query)
                self.conn.commit()
            except sqlite3.Error as e:
                print(f"Error creating table {table_name}: {e}")
                exit(1)
    
    @staticmethod
    def hashPassword(password: str) -> bytes:
        pw_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(pw_bytes, salt)

        return password_hash

    def addUser(self, username: str, email: str, password: str) -> bool:
        try:
            self.cursor.execute(
                "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?, ?, ?);",
                (username, Database.hashPassword(password), email)
            )
            self.conn.commit()
            return True
        except:
            return False

    def verifyUser(self, username: str, password: str) -> int:
        try:
            # Extract Device PlotID
            self.cursor.execute("SELECT userID, password_hash FROM users WHERE username = ?;",
            (username,))
            
            output = self.cursor.fetchone()
            userID = output[0]
            password_hash = output[1]

        except sqlite3.Error as e:
            print(f"Error fetching device count: {e}")
            return -1

        if bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
            return userID
        else:
            return -1
        
    def getUsername(self, userID) -> str:
        try:
            # Extract Device PlotID
            self.cursor.execute("SELECT username FROM users WHERE userID = ?;",
            (userID,))
            
            return self.cursor.fetchone()[0]
        except:
            print(f"Unknown User with ID: {userID}")
            return ""
    
@auth_bp.route('/register', methods=('GET', 'POST'))
def register():
    db = get_auth_db()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not email:
            error = 'Email is required'

        if error is None:
            if db.addUser(username, email, password):
                return redirect(url_for("auth.login"))
            else:
                error = f"User {username} is already registered."

        flash(error)

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=('GET', 'POST'))
def login():
    db = get_auth_db()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        error = None

        if not username:
            error = 'Username is required.'

        if error is None:
            result = db.verifyUser(username, password)
            if result != -1:
                session.clear()
                session['user_id'] = result
                return redirect(url_for('index'))
            else:
                error = 'Incorrect password.'

        flash(error)

    return render_template('auth/login.html')

@auth_bp.before_app_request
def load_logged_in_user():
    db = get_auth_db()
    userID = session.get('user_id')

    if userID is None:
        g.user = None
    else:
        g.user = db.getUsername(userID)

@auth_bp.route('/logout')
def logout():
    print("called logout")
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

def get_auth_db():
    if "auth_db" not in g:
        g.auth_db = Database(current_app.config["AUTH_DB"])
    return g.auth_db

def close_auth_db(e=None):
    db = g.pop("auth_db", None)
    if db is not None:
        db.close()