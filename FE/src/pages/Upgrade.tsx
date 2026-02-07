import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { createPayment } from '../services/payment';
import { getMyProfile } from '../services/user';
import '../styles/Upgrade.css';

interface VipPackage {
  id: number;
  name: string;
  price: number;
  durationDays: number;
  features: string[];
}

const PACKAGES: VipPackage[] = [
  {
    id: 1, // Silver
    name: 'Silver',
    price: 100000,
    durationDays: 30,
    features: ['Exclusive Market Insights', 'Ad-free Experience', 'Advanced Charts', 'Max candle limit: 1000'],
  },
  {
    id: 2, // Gold
    name: 'Gold',
    price: 1000000,
    durationDays: 365,
    features: ['All Silver Privileges', 'Priority Support', 'Max candle limit: 1500', 'Save 17% vs Monthly'],
  },
];

export const Upgrade = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [vipExpiration, setVipExpiration] = useState<string | null>(null);

  useEffect(() => {
    fetchUserProfile();
    const responseCode = searchParams.get('vnp_ResponseCode');
    if (responseCode === '00') {
      alert('Payment Successful! You have been upgraded to VIP.');
      localStorage.setItem('role', 'VIP'); // Optimistic update
      navigate('/');
    } else if (responseCode) {
      setError('Payment failed or cancelled.');
    }
  }, [searchParams, navigate]);

  const fetchUserProfile = async () => {
    const profile = await getMyProfile();
    if (profile && profile.vipEndAt) {
      // Format date: DD/MM/YYYY
      const date = new Date(profile.vipEndAt);
      setVipExpiration(date.toLocaleDateString('en-GB'));
    }
  };

  const handleUpgrade = async (pkg: VipPackage) => {
    setLoading(true);
    setError(null);
    try {
      const paymentUrl = await createPayment(pkg.id, 'VNPAY');
      if (paymentUrl) {
        window.location.href = paymentUrl;
      } else {
        setError('Could not create payment link.');
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred while creating payment.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);
  };

  return (
    <div className="upgrade-container">
      <div className="upgrade-content">
        <h1 className="upgrade-title">Upgrade to VIP</h1>

        {vipExpiration && (
          <div className="vip-status-banner">
            You are currently a VIP member. Expires on: <strong>{vipExpiration}</strong>
            <br />
            <small>Purchasing a new package will extend your duration.</small>
          </div>
        )}

        {error && <div className="error-message" style={{ marginBottom: '20px' }}>{error}</div>}

        <div className="packages-grid">
          {PACKAGES.map((pkg) => (
            <div key={pkg.id} className="package-card">
              <h2 className="package-name">{pkg.name}</h2>
              <div className="package-price">{formatCurrency(pkg.price)} / {pkg.durationDays} days</div>
              <ul className="package-features">
                {pkg.features.map((feature, index) => (
                  <li key={index} className={feature.includes('Save 17%') ? 'feature-savings' : ''}>
                    {feature === 'all_silver' ? <strong>All Silver Privileges</strong> : feature}
                  </li>
                ))}
              </ul>
              <button
                className="upgrade-btn"
                onClick={() => handleUpgrade(pkg)}
                disabled={loading}
              >
                {loading ? 'Processing...' : (vipExpiration ? 'Extend VIP' : 'Pay with VNPay')}
              </button>
            </div>
          ))}
        </div>
        <button className="back-btn" onClick={() => navigate('/')} style={{ marginTop: '2rem', padding: '10px 20px', background: 'transparent', border: '1px solid #fff', color: '#fff', borderRadius: '4px', cursor: 'pointer' }}>
          Back to Dashboard
        </button>
      </div>
    </div>
  );
};
