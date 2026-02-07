export const getMyProfile = async () => {
  const API_BASE = import.meta.env.VITE_API_BASE || '';
  const token = localStorage.getItem('accessToken');
  if (!token) return null;

  try {
    const response = await fetch(`${API_BASE}/api/v1/users/my-profile`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      // Handle 404 or other errors gracefully
      if (response.status === 404) return null;
      throw new Error('Failed to fetch profile');
    }

    const data = await response.json();
    return data.data;
  } catch (error) {
    console.error('Error fetching profile:', error);
    return null;
  }
};
