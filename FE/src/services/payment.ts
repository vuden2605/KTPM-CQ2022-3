export const createPayment = async (vipPackageId: number, method: string) => {
  const API_BASE = import.meta.env.VITE_API_BASE || '';
  const token = localStorage.getItem('accessToken');

  const response = await fetch(`${API_BASE}/api/v1/payments`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ vipPackageId, paymentMethod: method }),
  });

  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.message || 'Payment creation failed');
  }
  return result.data; // This should be the payment URL
};
