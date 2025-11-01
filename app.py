from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import psycopg2
import psycopg2.extras
import os
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database URL from Render environment
DATABASE_URL = os.environ.get("DATABASE_URL")

# OpenAI API configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize OpenAI client
try:
    if OPENAI_API_KEY and OPENAI_API_KEY.strip():
        openai_client = OpenAI(api_key=OPENAI_API_KEY.strip())
        print("OpenAI API настроен успешно.")
    else:
        print("Внимание: OPENAI_API_KEY не установлен в переменных окружения!")
        openai_client = None
except Exception as e:
    print(f"Ошибка при настройке OpenAI API: {e}")
    openai_client = None

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
            # Check if this is an API request (JSON expected)
            if request.path.startswith('/api/') or request.is_json:
                return jsonify({'error': 'Требуется авторизация', 'auth_required': True}), 401
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


@app.route('/api/test-openai')
@login_required
def test_openai():
    """Тестовый эндпоинт для проверки работы OpenAI API"""
    try:
        if not openai_client:
            return jsonify({'error': 'OpenAI клиент не инициализирован', 'key_set': False}), 500
        
        if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
            return jsonify({'error': 'API ключ не настроен', 'key_set': False}), 500
        
        # Try simple API call with ChatGPT
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Скажи привет одним словом"}
            ],
            max_tokens=50
        )
        
        return jsonify({
            'status': 'success',
            'message': 'ChatGPT API работает!',
            'response': response.choices[0].message.content,
            'model': response.model
        })
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        
        # Check for API key related errors
        if 'api' in error_msg.lower() and 'key' in error_msg.lower() or 'authentication' in error_msg.lower():
            return jsonify({
                'error': 'Неверный API ключ',
                'details': error_msg,
                'error_type': error_type,
                'key_set': bool(OPENAI_API_KEY)
            }), 500
        elif '403' in error_msg or 'forbidden' in error_msg.lower():
            return jsonify({
                'error': 'Доступ запрещен. Проверьте API ключ и права доступа.',
                'details': error_msg,
                'error_type': error_type
            }), 500
        elif '429' in error_msg or 'quota' in error_msg.lower() or 'limit' in error_msg.lower():
            return jsonify({
                'error': 'Достигнут лимит запросов. Попробуйте позже.',
                'details': error_msg,
                'error_type': error_type
            }), 500
        elif 'insufficient_quota' in error_msg.lower() or 'billing' in error_msg.lower():
            return jsonify({
                'error': 'Недостаточно средств на счету OpenAI. Пополните баланс.',
                'details': error_msg,
                'error_type': error_type
            }), 500
        else:
            return jsonify({
                'error': f'Ошибка при тестировании: {error_msg}',
                'error_type': error_type
            }), 500


@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        history = data.get('history', [])
        
        if not message:
            return jsonify({'error': 'Сообщение не может быть пустым'}), 400
        
        if not openai_client:
            return jsonify({'error': 'OpenAI клиент не инициализирован'}), 500
        
        # Build messages array for OpenAI API
        messages = []
        
        # Add conversation history if available
        if history and len(history) > 0:
            for msg in history[-20:]:  # Keep last 20 messages for context
                if msg.get('content'):
                    role = 'user' if msg.get('isUser') else 'assistant'
                    messages.append({
                        'role': role,
                        'content': msg.get('content', '')
                    })
        
        # Add current message
        messages.append({
            'role': 'user',
            'content': message
        })
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Using gpt-4o-mini as default, can be changed to gpt-4, gpt-3.5-turbo, etc.
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        response_text = response.choices[0].message.content
        
        return jsonify({
            'response': response_text
        })
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        # Log full error for debugging
        print(f"Chat API Error [{error_type}]: {error_msg}")
        
        # Provide user-friendly error messages based on error content
        error_lower = error_msg.lower()
        
        if 'api' in error_lower and 'key' in error_lower or 'authentication' in error_lower:
            return jsonify({'error': 'Неверный API ключ. Проверьте правильность ключа OpenAI API.', 'details': error_msg}), 500
        elif '403' in error_msg or 'forbidden' in error_lower or 'permission' in error_lower:
            return jsonify({'error': 'Нет доступа к API. Проверьте права доступа ключа.', 'details': error_msg}), 500
        elif '429' in error_msg or 'quota' in error_lower or 'limit' in error_lower or 'rate' in error_lower:
            return jsonify({'error': 'Достигнут лимит запросов. Попробуйте позже.', 'details': error_msg}), 500
        elif '404' in error_msg or 'not found' in error_lower:
            return jsonify({'error': 'Модель не найдена. Проверьте название модели.', 'details': error_msg}), 500
        elif 'insufficient_quota' in error_lower or 'billing' in error_lower:
            return jsonify({'error': 'Недостаточно средств на счету OpenAI. Пополните баланс.', 'details': error_msg}), 500
        else:
            return jsonify({'error': f'Ошибка ChatGPT API: {error_msg}', 'error_type': error_type}), 500


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
