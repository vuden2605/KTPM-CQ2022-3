import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../App.css';

interface User {
  id: number;
  userName: string;
  email: string;
  role: 'USER' | 'ADMIN' | 'VIP';
  vipStartAt?: string;
  vipEndAt?: string;
}

export const AdminDashboard = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const API_BASE = import.meta.env.VITE_API_BASE || '';

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        navigate('/login');
        return;
      }

      const response = await fetch(`${API_BASE}/api/v1/users`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        setUsers(result.data);
      } else {
        if (response.status === 403) {
          setError('Access Denied: You are not an Admin');
        } else {
          setError('Failed to fetch users');
        }
      }
    } catch (err) {
      setError('Error connecting to server');
    } finally {
      setLoading(false);
    }
  };

  const toggleVip = async (userId: number) => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${API_BASE}/api/v1/users/${userId}/vip-toggle`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        // Refresh list or update local state
        fetchUsers();
        alert('VIP status updated');
      } else {
        alert('Failed to update VIP status');
      }
    } catch (e) {
      alert('Error updating VIP status');
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [navigate]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div style={{ color: 'red', padding: '20px' }}>{error}</div>;

  return (
    <div style={{ padding: '20px', color: '#fff' }}>
      <h1>Admin Dashboard</h1>
      <button onClick={() => navigate('/')} style={{ marginBottom: '20px', padding: '10px' }}>Back to Dashboard</button>

      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '20px' }}>
        <thead>
          <tr style={{ background: '#333', textAlign: 'left' }}>
            <th style={{ padding: '10px' }}>ID</th>
            <th style={{ padding: '10px' }}>Username</th>
            <th style={{ padding: '10px' }}>Email</th>
            <th style={{ padding: '10px' }}>Role</th>
            <th style={{ padding: '10px' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map(user => (
            <tr key={user.id} style={{ borderBottom: '1px solid #444' }}>
              <td style={{ padding: '10px' }}>{user.id}</td>
              <td style={{ padding: '10px' }}>{user.userName}</td>
              <td style={{ padding: '10px' }}>{user.email}</td>
              <td style={{ padding: '10px' }}>{user.role}</td>
              <td style={{ padding: '10px' }}>
                <button
                  onClick={() => toggleVip(user.id)}
                  style={{
                    padding: '5px 10px',
                    background: user.role === 'VIP' ? '#e74c3c' : '#2ecc71',
                    border: 'none',
                    color: 'white',
                    cursor: 'pointer',
                    borderRadius: '4px'
                  }}
                  disabled={user.role === 'ADMIN'}
                >
                  {user.role === 'VIP' ? 'Revoke VIP' : 'Make VIP'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
