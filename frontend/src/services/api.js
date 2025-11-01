// API URL configuration
// Uses relative path '/api' which works in both:
// - Development: React dev server proxies to backend (see package.json proxy)
// - Production/Docker: nginx proxies to backend (see Dockerfile nginx config)
// Override with REACT_APP_API_URL environment variable if needed
const API_URL = process.env.REACT_APP_API_URL || '/api';

export const checkAuth = async () => {
  const response = await fetch(`${API_URL}/check-auth`, {
    method: 'GET',
    credentials: 'include',
  });
  return response.json();
};

export const register = async (username, email, password, confirmPassword) => {
  const response = await fetch(`${API_URL}/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ username, email, password, confirm_password: confirmPassword }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Ошибка регистрации');
  }
  return data;
};

export const login = async (username, password) => {
  const response = await fetch(`${API_URL}/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Ошибка входа');
  }
  return data;
};

export const logout = async () => {
  const response = await fetch(`${API_URL}/logout`, {
    method: 'POST',
    credentials: 'include',
  });
  return response.json();
};

export const getDashboard = async () => {
  const response = await fetch(`${API_URL}/dashboard`, {
    method: 'GET',
    credentials: 'include',
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Ошибка загрузки данных');
  }
  return data;
};

