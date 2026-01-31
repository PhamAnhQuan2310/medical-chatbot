import React, { useState, useEffect } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Auth.css';

axios.defaults.baseURL = 'http://localhost:8000';
axios.defaults.withCredentials = true;

interface AuthFormProps {
  isLogin: boolean;
}

const AuthForm: React.FC<AuthFormProps> = ({ isLogin }) => {
  const [username, setUsername] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const navigate = useNavigate();

  useEffect(() => {
    setUsername('');
    setEmail('');
    setPassword('');
    setError('');
    setIsLoading(false);
  }, [isLogin]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const endpoint = isLogin ? '/login/' : '/register/';
      const data = isLogin
        ? { username, password }
        : { username, email, password };

      const response = await axios.post(endpoint, data, {
        headers: { 'Content-Type': 'application/json' },
      });

      if (response.data.status === 'success') {
        if (isLogin && response.data.user) {
          // Save user data to localStorage
          localStorage.setItem('user', JSON.stringify(response.data.user));
          
          // Navigate to main page
          navigate('/');
          
          // Reload page to trigger user context update
          window.location.reload();
        } else {
          // Registration successful, redirect to login
          navigate('/login');
        }
      } else {
        setError(response.data.detail || response.data.error || 'An error occurred. Please try again.');
      }
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Failed to connect to the server. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-form">
        <h2 className="auth-title">{isLogin ? 'Đăng Nhập' : 'Đăng Ký'}</h2>
        {error && <div className="auth-error">{error}</div>}
        <form onSubmit={handleSubmit} className="auth-form-content">
          <div className="form-group">
            <label htmlFor="username" className="form-label">
              Tên người dùng
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="form-input"
              placeholder="Nhập tên người dùng"
              required
            />
          </div>
          {!isLogin && (
            <div className="form-group">
              <label htmlFor="email" className="form-label">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="form-input"
                placeholder="Nhập email của bạn"
                required
              />
            </div>
          )}
          <div className="form-group">
            <label htmlFor="password" className="form-label">
              Mật khẩu
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="form-input"
              placeholder="Nhập mật khẩu"
              required
            />
          </div>
          <button
            type="submit"
            className={`auth-button ${isLoading ? 'loading' : ''}`}
            disabled={isLoading}
          >
            {isLoading ? (
              <svg
                className="spinner"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <circle
                  className="spinner-path"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
              </svg>
            ) : (
              isLogin ? 'Đăng Nhập' : 'Đăng Ký'
            )}
          </button>
        </form>
        <p className="auth-footer">
          {isLogin ? 'Chưa có tài khoản?' : 'Đã có tài khoản?'}{' '}
          <Link
            to={isLogin ? '/register' : '/login'}
            className="auth-link"
          >
            {isLogin ? 'Đăng ký ngay' : 'Đăng nhập'}
          </Link>
        </p>
        <p className="auth-footer">
          <Link to="/guest" className="auth-link">
            Trải nghiệm chat khách (Guest)
          </Link>
        </p>
      </div>
    </div>
  );
};

const Auth: React.FC = () => {
  const location = useLocation();
  if (location.pathname === '/register') {
    return <AuthForm isLogin={false} />;
  }
  // Mặc định hiển thị đăng nhập cho /login và các đường dẫn khác
  return <AuthForm isLogin={true} />;
};

export default Auth;