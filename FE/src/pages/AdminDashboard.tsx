import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/AdminDashboard.css';

interface User {
  id: number;
  userName: string;
  email: string;
  role: 'ADMIN' | 'USER' | 'VIP';
  isActive: boolean;
  vipEndAt?: string;
}

export const AdminDashboard = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchUsers = async () => {
    try {
      const accessToken = localStorage.getItem('accessToken');
      const API_BASE = (import.meta.env.VITE_API_BASE as string) || 'http://localhost:80';

      const response = await fetch(`${API_BASE}/api/v1/users`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        if (response.status === 403) {
          setError('Bạn không có quyền truy cập trang này');
        } else {
          setError('Lấy danh sách người dùng thất bại');
        }
        return;
      }

      const result = await response.json();
      setUsers(result.data);
    } catch (err) {
      setError('Lỗi kết nối đến server');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleToggleVip = async (userId: number, currentRole: string) => {
    if (currentRole === 'ADMIN') return;

    try {
      const accessToken = localStorage.getItem('accessToken');
      const API_BASE = (import.meta.env.VITE_API_BASE as string) || 'http://localhost:80';

      const response = await fetch(`${API_BASE}/api/v1/users/${userId}/vip-toggle`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        // Update local state to reflect change immediately
        setUsers(users.map(u => u.id === userId ? {
          ...u,
          role: result.data.role,
          vipEndAt: result.data.vipEndAt
        } : u));
      } else {
        alert('Cập nhật thất bại');
      }
    } catch (e) {
      console.error(e);
      alert('Lỗi kết nối');
    }
  };

  if (loading) return <div className="loading-container">Đang tải dữ liệu...</div>;

  return (
    <div className="app">
      {/* Header */}
      <div className="app-header">
        <div className="header-left">
          <div className="app-logo" style={{ cursor: 'pointer' }} onClick={() => navigate('/')}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#2962ff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M2 17L12 22L22 17" stroke="#2962ff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M2 12L12 17L22 12" stroke="#2962ff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>TradeScope Admin</span>
          </div>
        </div>
        <div className="header-right" style={{ gap: '12px' }}>
          <button
            className="nav-btn"
            onClick={() => navigate('/')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            ← Back to Dashboard
          </button>

          <button className="logout-btn" onClick={() => {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('role');
            localStorage.removeItem('aiAnalysisState');
            navigate('/login');
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ marginRight: 6 }}>
              <path d="M17 16L21 12M21 12L17 8M21 12L7 12M13 16V17C13 18.6569 11.6569 20 10 20H6C4.34315 20 3 18.6569 3 17V7C3 5.34315 4.34315 4 6 4H10C11.6569 4 13 5.34315 13 7V8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Logout
          </button>
        </div>
      </div>

      <div className="app-content" style={{ flexDirection: 'column', padding: '20px', overflowY: 'auto' }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto', width: '100%' }}>
          <h1 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '24px' }}>Manage Users</h1>

          {error && <div className="error-message">{error}</div>}

          <div className="admin-table-container">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>VIP Access</th>
                  <th>Expiration</th>
                </tr>
              </thead>
              <tbody>
                {users.map(user => (
                  <tr key={user.id}>
                    <td>{user.id}</td>
                    <td>{user.userName}</td>
                    <td>{user.email}</td>
                    <td>
                      <span className={`role-badge role-${user.role.toLowerCase()}`}>
                        {user.role}
                      </span>
                    </td>
                    <td>
                      {user.role !== 'ADMIN' && (
                        <label className="switch">
                          <input
                            type="checkbox"
                            checked={user.role === 'VIP'}
                            onChange={() => handleToggleVip(user.id, user.role)}
                          />
                          <span className="slider"></span>
                        </label>
                      )}
                    </td>
                    <td>
                      {user.vipEndAt ? new Date(user.vipEndAt).toLocaleDateString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
