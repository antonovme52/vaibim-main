import React from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

function Navbar({ user, setUser }) {
  return (
    <nav>
      <ul>
        <li className="logo">
          <Link to="/">Flask Auth</Link>
        </li>
        {user ? (
          <>
            <li className="nav-right">
              <Link to="/dashboard">Панель управления</Link>
            </li>
            <li>
              <Link to="/logout" onClick={async (e) => {
                e.preventDefault();
                try {
                  const { logout } = await import('../services/api');
                  await logout();
                  setUser(null);
                  window.location.href = '/';
                } catch (error) {
                  console.error('Ошибка выхода:', error);
                }
              }}>
                Выход
              </Link>
            </li>
          </>
        ) : (
          <>
            <li className="nav-right">
              <Link to="/login">Вход</Link>
            </li>
            <li>
              <Link to="/register">Регистрация</Link>
            </li>
          </>
        )}
      </ul>
    </nav>
  );
}

export default Navbar;

