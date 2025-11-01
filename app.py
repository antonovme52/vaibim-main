from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import psycopg2
import psycopg2.extras
import os
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database URL from Render environment
DATABASE_URL = os.environ.get("DATABASE_URL")

# Gemini API configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDXvXzD2xqmsWQFv2FqnyYD9ER22qbkIgY")
genai.configure(api_key=GEMINI_API_KEY)

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.after_request
def add_header(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    response.headers['User-Agent'] = 'MyApp'
    return response

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not email or not password:
            flash('Все поля обязательны для заполнения', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
                (username, email, hashed_password))
            conn.commit()
            cur.close()
            conn.close()
            flash('Регистрация успешна!', 'success')
            return redirect(url_for('login'))
        except psycopg2.Error:
            flash('Пользователь уже существует', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash('Ошибка входа', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('dashboard.html', user=user)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        history = data.get('history', [])
        
        if not message:
            return jsonify({'error': 'Сообщение не может быть пустым'}), 400
        
        # Try to use the latest model, fallback to gemini-pro
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
        except:
            try:
                model = genai.GenerativeModel('gemini-1.5-pro')
            except:
                model = genai.GenerativeModel('gemini-pro')
        
        # Build conversation context if history is provided
        if history and len(history) > 0:
            # Convert history to the format expected by Gemini
            chat_history = []
            for msg in history[-10:]:  # Keep last 10 messages for context
                role = 'user' if msg.get('isUser') else 'model'
                chat_history.append({
                    'role': role,
                    'parts': [msg.get('content', '')]
                })
            
            # Start a chat session with history
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(message)
        else:
            # Simple single message
            response = model.generate_content(message)
        
        return jsonify({
            'response': response.text
        })
    except Exception as e:
        error_msg = str(e)
        # Provide user-friendly error messages
        if 'API_KEY' in error_msg or 'api' in error_msg.lower():
            error_msg = 'Ошибка API ключа. Проверьте настройки.'
        elif 'quota' in error_msg.lower() or 'limit' in error_msg.lower():
            error_msg = 'Достигнут лимит запросов. Попробуйте позже.'
        return jsonify({'error': f'Ошибка: {error_msg}'}), 500


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
