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

# Configure Gemini API
try:
    if GEMINI_API_KEY and GEMINI_API_KEY.strip():
        genai.configure(api_key=GEMINI_API_KEY.strip())
        print(f"Gemini API настроен. Ключ: {GEMINI_API_KEY[:10]}...")
    else:
        print("Внимание: GEMINI_API_KEY не установлен!")
except Exception as e:
    print(f"Ошибка при настройке Gemini API: {e}")

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


@app.route('/api/test-gemini')
@login_required
def test_gemini():
    """Тестовый эндпоинт для проверки работы Gemini API"""
    try:
        if not GEMINI_API_KEY or not GEMINI_API_KEY.strip():
            return jsonify({'error': 'API ключ не настроен', 'key_set': False}), 500
        
        # Try simple API call
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Скажи привет одним словом")
        
        return jsonify({
            'status': 'success',
            'message': 'Gemini API работает!',
            'response': response.text,
            'key_preview': f"{GEMINI_API_KEY[:10]}...",
            'key_length': len(GEMINI_API_KEY)
        })
    except genai.errors.InvalidAPIKeyError as e:
        return jsonify({
            'error': 'Неверный API ключ',
            'details': str(e),
            'key_preview': f"{GEMINI_API_KEY[:10]}..." if GEMINI_API_KEY else "не установлен"
        }), 500
    except Exception as e:
        return jsonify({
            'error': f'Ошибка при тестировании: {str(e)}',
            'error_type': type(e).__name__
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
        
        # Verify API key is configured and re-configure if needed
        api_key = GEMINI_API_KEY.strip() if GEMINI_API_KEY else None
        if not api_key or api_key == '':
            return jsonify({'error': 'API ключ не настроен. Установите GEMINI_API_KEY'}), 500
        
        # Re-configure API key to ensure it's set correctly
        try:
            genai.configure(api_key=api_key)
        except Exception as config_error:
            return jsonify({'error': f'Ошибка конфигурации API: {str(config_error)}'}), 500
        
        # Try to use the latest model, fallback to gemini-pro
        model = None
        model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                # Test if model works by trying to access it
                break
            except Exception as model_error:
                if model_name == model_names[-1]:  # Last model, raise the error
                    raise model_error
                continue
        
        if model is None:
            return jsonify({'error': 'Не удалось инициализировать модель Gemini'}), 500
        
        # Build conversation context if history is provided
        if history and len(history) > 0:
            # Convert history to the format expected by Gemini
            chat_history = []
            for msg in history[-10:]:  # Keep last 10 messages for context
                if msg.get('content'):
                    role = 'user' if msg.get('isUser') else 'model'
                    chat_history.append({
                        'role': role,
                        'parts': [msg.get('content', '')]
                    })
            
            # Start a chat session with history
            if chat_history:
                chat = model.start_chat(history=chat_history)
                response = chat.send_message(message)
            else:
                # No valid history, use simple generate
                response = model.generate_content(message)
        else:
            # Simple single message
            response = model.generate_content(message)
        
        # Extract text from response
        if hasattr(response, 'text'):
            response_text = response.text
        elif hasattr(response, 'parts'):
            response_text = ''.join([part.text for part in response.parts if hasattr(part, 'text')])
        else:
            response_text = str(response)
        
        return jsonify({
            'response': response_text
        })
    except genai.errors.InvalidAPIKeyError as e:
        return jsonify({'error': f'Неверный API ключ. Проверьте правильность ключа Gemini API.'}), 500
    except genai.errors.APIError as e:
        error_msg = str(e)
        if 'quota' in error_msg.lower() or 'limit' in error_msg.lower():
            return jsonify({'error': 'Достигнут лимит запросов. Попробуйте позже.'}), 500
        elif 'permission' in error_msg.lower() or 'forbidden' in error_msg.lower():
            return jsonify({'error': 'Нет доступа к API. Проверьте права доступа ключа.'}), 500
        return jsonify({'error': f'Ошибка Gemini API: {error_msg}'}), 500
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        # Log full error for debugging (you can add logging here)
        print(f"Chat API Error [{error_type}]: {error_msg}")
        
        # Provide user-friendly error messages
        if 'API_KEY' in error_msg or 'api' in error_msg.lower() or 'key' in error_msg.lower():
            return jsonify({'error': f'Ошибка API ключа: {error_msg}'}), 500
        elif 'quota' in error_msg.lower() or 'limit' in error_msg.lower():
            return jsonify({'error': 'Достигнут лимит запросов. Попробуйте позже.'}), 500
        else:
            return jsonify({'error': f'Ошибка: {error_msg}'}), 500


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
