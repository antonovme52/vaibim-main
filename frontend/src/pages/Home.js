import React from 'react';
import { Link } from 'react-router-dom';

function Home({ user }) {
  return (
    <div className="container">
      <div className="card">
        <h1>Добро пожаловать!</h1>
        <p style={{ textAlign: 'center', color: '#8b949e', marginBottom: '2rem', fontSize: '1.1rem' }}>
          Это приложение с авторизацией на Flask и React
        </p>
        
        {!user && (
          <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem', flexWrap: 'wrap' }}>
            <Link to="/login" style={{ flex: 1, minWidth: '150px', textDecoration: 'none' }}>
              <button className="btn">Войти</button>
            </Link>
            <Link to="/register" style={{ flex: 1, minWidth: '150px', textDecoration: 'none' }}>
              <button className="btn btn-primary">Регистрация</button>
            </Link>
          </div>
        )}

        {user && (
          <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem', flexWrap: 'wrap' }}>
            <Link to="/dashboard" style={{ flex: 1, minWidth: '150px', textDecoration: 'none' }}>
              <button className="btn">Перейти в панель управления</button>
            </Link>
          </div>
        )}

        <div style={{ marginTop: '3rem', padding: '2rem', background: 'rgba(88, 166, 255, 0.05)', border: '1px solid rgba(88, 166, 255, 0.2)', borderRadius: '12px' }}>
          <h3 style={{ color: '#f0f6fc', marginBottom: '1.5rem', fontWeight: 600 }}>Возможности:</h3>
          <ul style={{ color: '#c9d1d9', lineHeight: 2.5, listStyle: 'none', paddingLeft: 0 }}>
            <li style={{ marginBottom: '0.75rem' }}>✅ Безопасная регистрация пользователей</li>
            <li style={{ marginBottom: '0.75rem' }}>✅ Авторизация с хешированием паролей</li>
            <li style={{ marginBottom: '0.75rem' }}>✅ Защищенные страницы</li>
            <li style={{ marginBottom: '0.75rem' }}>✅ Современный интерфейс в стиле Cursor</li>
          </ul>
        </div>

        <div style={{ marginTop: '2rem', padding: '2rem', background: 'rgba(188, 140, 255, 0.05)', border: '1px solid rgba(188, 140, 255, 0.2)', borderRadius: '12px' }}>
          <h3 style={{ color: '#f0f6fc', marginBottom: '1.5rem', fontWeight: 600 }}>🛠 Стек технологий:</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <div style={{ padding: '1rem', background: 'rgba(88, 166, 255, 0.1)', borderRadius: '8px', border: '1px solid rgba(88, 166, 255, 0.2)' }}>
              <div style={{ color: '#58a6ff', fontWeight: 600, marginBottom: '0.5rem' }}>Backend</div>
              <div style={{ color: '#c9d1d9', fontSize: '0.9rem' }}>Flask 3.0.0</div>
              <div style={{ color: '#c9d1d9', fontSize: '0.9rem' }}>Python 3.12</div>
              <div style={{ color: '#c9d1d9', fontSize: '0.9rem' }}>Werkzeug 3.0.1</div>
            </div>
            <div style={{ padding: '1rem', background: 'rgba(188, 140, 255, 0.1)', borderRadius: '8px', border: '1px solid rgba(188, 140, 255, 0.2)' }}>
              <div style={{ color: '#bc8cff', fontWeight: 600, marginBottom: '0.5rem' }}>База данных</div>
              <div style={{ color: '#c9d1d9', fontSize: '0.9rem' }}>PostgreSQL</div>
              <div style={{ color: '#c9d1d9', fontSize: '0.9rem' }}>psycopg2-binary</div>
            </div>
            <div style={{ padding: '1rem', background: 'rgba(255, 107, 157, 0.1)', borderRadius: '8px', border: '1px solid rgba(255, 107, 157, 0.2)' }}>
              <div style={{ color: '#ff6b9d', fontWeight: 600, marginBottom: '0.5rem' }}>DevOps</div>
              <div style={{ color: '#c9d1d9', fontSize: '0.9rem' }}>Docker</div>
              <div style={{ color: '#c9d1d9', fontSize: '0.9rem' }}>Docker Compose</div>
            </div>
            <div style={{ padding: '1rem', background: 'rgba(46, 160, 67, 0.1)', borderRadius: '8px', border: '1px solid rgba(46, 160, 67, 0.2)' }}>
              <div style={{ color: '#3fb950', fontWeight: 600, marginBottom: '0.5rem' }}>Frontend</div>
              <div style={{ color: '#c9d1d9', fontSize: '0.9rem' }}>React 18.2.0</div>
              <div style={{ color: '#c9d1d9', fontSize: '0.9rem' }}>React Router 6.20.0</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;

