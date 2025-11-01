from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Add response headers to bypass ngrok warning
@app.after_request
def add_header(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    response.headers['User-Agent'] = 'MyApp'
    return response

# Database configuration
DATABASE = 'users.db'

def get_db_connection():
    """Create a database connection with timeout"""
    conn = sqlite3.connect(DATABASE, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrency
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

def init_db():
    """Initialize the database"""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def login_required(f):
    """Decorator to require login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Home page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validation
        if not username or not email or not password:
            flash('Все поля обязательны для заполнения', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Пароль должен быть не менее 6 символов', 'danger')
            return redirect(url_for('register'))

        # Hash password
        hashed_password = generate_password_hash(password)

        conn = None
        try:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, hashed_password)
            )
            conn.commit()
            flash('Регистрация успешна! Теперь вы можете войти', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Пользователь с таким именем или email уже существует', 'danger')
            return redirect(url_for('register'))
        except sqlite3.OperationalError as e:
            flash(f'Ошибка базы данных: {str(e)}', 'danger')
            return redirect(url_for('register'))
        finally:
            if conn:
                conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Введите имя пользователя и пароль', 'danger')
            return redirect(url_for('login'))

        conn = None
        try:
            conn = get_db_connection()
            user = conn.execute(
                'SELECT * FROM users WHERE username = ?', (username,)
            ).fetchone()

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash(f'Добро пожаловать, {user["username"]}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Неверное имя пользователя или пароль', 'danger')
                return redirect(url_for('login'))
        except sqlite3.OperationalError as e:
            flash(f'Ошибка базы данных: {str(e)}', 'danger')
            return redirect(url_for('login'))
        finally:
            if conn:
                conn.close()

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard (protected route)"""
    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE id = ?', (session['user_id'],)
        ).fetchone()
        return render_template('dashboard.html', user=user)
    except sqlite3.OperationalError as e:
        flash(f'Ошибка базы данных: {str(e)}', 'danger')
        return redirect(url_for('index'))
    finally:
        if conn:
            conn.close()

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
