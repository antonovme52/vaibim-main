import React from 'react';
import { useNavigate, Link } from 'react-router-dom';

function Dashboard({ user }) {
  const navigate = useNavigate();

  if (!user) {
    return null;
  }

  return (
    <div className="container">
      <div className="dashboard-card">
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h2 style={{ color: '#8b949e', fontSize: '1rem', fontWeight: 400, marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            Добро пожаловать
          </h2>
          <div className="username-display">{user.username}</div>
        </div>
        
        <div style={{ background: '#0d1117', border: '1px solid #30363d', padding: '2rem', borderRadius: '12px', marginBottom: '2rem' }}>
          <h3 style={{ marginBottom: '1.5rem', color: '#58a6ff', fontSize: '1.1rem', fontWeight: 600 }}>👤 Информация о пользователе</h3>
          <p style={{ marginBottom: '1rem', color: '#8b949e', fontSize: '0.95rem' }}>
            <strong style={{ color: '#c9d1d9' }}>ID:</strong> {user.id}
          </p>
          <p style={{ marginBottom: '1rem', color: '#8b949e', fontSize: '0.95rem' }}>
            <strong style={{ color: '#c9d1d9' }}>Email:</strong> {user.email}
          </p>
          <p style={{ marginBottom: '1rem', color: '#8b949e', fontSize: '0.95rem' }}>
            <strong style={{ color: '#c9d1d9' }}>Дата регистрации:</strong> {new Date(user.created_at).toLocaleString('ru-RU')}
          </p>
        </div>

        <div style={{ background: 'rgba(88, 166, 255, 0.05)', border: '1px solid rgba(88, 166, 255, 0.2)', padding: '2rem', borderRadius: '12px', marginBottom: '2rem' }}>
          <h3 style={{ color: '#f0f6fc', marginBottom: '1rem', fontWeight: 600 }}>🎉 Добро пожаловать!</h3>
          <p style={{ color: '#8b949e', lineHeight: 1.6 }}>
            Вы успешно авторизовались в системе. Это защищенная страница, доступная только авторизованным пользователям.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <Link to="/" style={{ flex: 1, minWidth: '150px', textDecoration: 'none' }}>
            <button className="btn btn-secondary">На главную</button>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;

