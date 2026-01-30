import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/Login.css';

interface LoginResponse {
  code: number;
  message: string;
  data?: {
    accessToken?: string;
    refreshToken?: string;
    isAuthenticated?: boolean;
    role?: string;
  };
}

export const Login = () => {
  const navigate = useNavigate();
  const [userName, setUserName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const API_BASE = import.meta.env.VITE_API_BASE || '';
      const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userName, password }),
      });

      const result = (await response.json()) as LoginResponse;
      console.debug('Login response:', result);

      if (response.ok) {
        // Save tokens to localStorage if present
        if (result?.data?.accessToken) {
          localStorage.setItem('accessToken', result.data.accessToken);
        }
        if (result?.data?.refreshToken) {
          localStorage.setItem('refreshToken', result.data.refreshToken);
        }
        if (result?.data?.role) {
          localStorage.setItem('role', result.data.role);
        }

        // Navigate to main app
        navigate('/');
        return;
      }

      // Map backend messages to friendly Vietnamese messages
      const backendMsg = result?.message || '';
      if (backendMsg.toLowerCase().includes('unauthenticated') || backendMsg.toLowerCase().includes('user_not_found') || backendMsg.toLowerCase().includes('invalid')) {
        setError('Tên đăng nhập hoặc mật khẩu không đúng');
      } else {
        setError(backendMsg || 'Đăng nhập thất bại');
      }
    } catch (err) {
      setError('Lỗi kết nối đến server');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterClick = () => {
    navigate('/register');
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <h1>₿ Crypto Trading</h1>
          <p>Đăng nhập vào tài khoản của bạn</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="userName">Tên đăng nhập</label>
            <input
              id="userName"
              type="text"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              placeholder="Nhập tên đăng nhập"
              required
              autoComplete="username"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Mật khẩu</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Nhập mật khẩu"
              required
              autoComplete="current-password"
              disabled={loading}
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
          </button>

          <div className="register-section">
            <span>Chưa có tài khoản?</span>
            <button
              type="button"
              className="register-link"
              onClick={handleRegisterClick}
              disabled={loading}
            >
              Đăng ký ngay
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
