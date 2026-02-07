import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import '../styles/PaymentResult.css';

const PaymentResult = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'success' | 'error' | 'loading'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const responseCode = searchParams.get('vnp_ResponseCode');

    if (!responseCode) {
      setStatus('error');
      setMessage('Invalid payment response.');
      return;
    }

    const finalizePayment = async () => {
      try {
        const orderId = searchParams.get('vnp_TxnRef');
        // If not found, maybe it's vnp_OrderInfo? But we store orderId in vnp_TxnRef in VNPayProvider.

        if (responseCode === '00' && orderId) {
          const API_BASE = import.meta.env.VITE_API_BASE || '';
          const accessToken = localStorage.getItem('accessToken');

          const response = await fetch(`${API_BASE}/api/v1/payments/finalize?responseCode=${responseCode}&orderId=${orderId}`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json'
            }
          });

          if (response.ok) {
            setStatus('success');
            setMessage('Payment Successful! You are now a VIP member.');
            localStorage.setItem('role', 'VIP');
          } else {
            setStatus('error');
            setMessage('Payment verification failed.');
          }
        } else {
          setStatus('error');
          setMessage('Invalid payment response.');
        }
      } catch (e) {
        setStatus('error');
        setMessage('Error finalizing payment.');
      }
    };

    if (responseCode === '00') {
      finalizePayment();
    } else if (responseCode) {
      setStatus('error');
      setMessage('Payment failed or cancelled.');
    } else {
      setStatus('error');
      setMessage('Invalid payment response.');
    }
  }, [searchParams]);

  return (
    <div className="payment-result-container">
      <div className={`result-card ${status}`}>
        {status === 'loading' && <h2>Processing Payment...</h2>}

        {status === 'success' && (
          <>
            <div className="icon success-icon">✓</div>
            <h1>Payment Successful!</h1>
            <p>{message}</p>
            <button onClick={() => navigate('/')} className="action-btn">
              Go to Dashboard
            </button>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="icon error-icon">✕</div>
            <h1>Payment Failed</h1>
            <p>{message}</p>
            <div className="actions">
              <button onClick={() => navigate('/upgrade')} className="retry-btn">
                Try Again
              </button>
              <button onClick={() => navigate('/')} className="back-btn">
                Back to Dashboard
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default PaymentResult;
