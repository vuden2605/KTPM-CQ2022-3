import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/AdminDashboard.css';

interface User {
  id: number;
  userName: string;
  email: string;
  role: 'ADMIN' | 'USER' | 'VIP';
  isActive: boolean;
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
        setUsers(users.map(u => u.id === userId ? { ...u, role: result.data.role } : u));
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
    <div className="admin-container">
      <div className="admin-header">
        <h1 className="admin-title">Admin Dashboard</h1>
        <button className="back-btn" onClick={() => navigate('/')}>
          ← Quay lại Dashboard
        </button>
      </div>

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
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
