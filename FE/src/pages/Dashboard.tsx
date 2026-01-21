import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CandlestickChart } from '../components/CandlestickChart';
import { Watchlist } from '../components/Watchlist';
import '../App.css';

export const Dashboard = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [intervalLabel, setIntervalLabel] = useState('1m');
  const navigate = useNavigate();

  const handleLogout = async () => {
    const accessToken = localStorage.getItem('accessToken');
    try {
      const API_BASE = (import.meta.env.VITE_API_BASE as string) || 'http://localhost:8082';
      if (accessToken) {
        await fetch(`${API_BASE}/api/v1/auth/logout`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${accessToken}` },
          body: JSON.stringify({ accessToken }),
        });
      }
    } catch (e) {
      console.warn('Logout request failed', e);
    } finally {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      navigate('/login');
    }
  };

  const labelToSeconds = (label: string) => {
    const map: Record<string, number> = {
      '1m': 60,
      '5m': 300,
      '15m': 900,
      '1h': 3600,
      '4h': 14400,
      '1d': 86400,
    };
    return map[label] ?? 86400;
  };

  return (
    <div className="app">
      {/* Full-width header */}
      <div className="app-header">
        <h2>{selectedSymbol}</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div className="chart-controls">
            {['1m', '5m', '15m', '1h', '4h', '1d'].map((lbl) => (
              <button
                key={lbl}
                className={`interval-btn ${intervalLabel === lbl ? 'active' : ''}`}
                onClick={() => setIntervalLabel(lbl)}
              >
                {lbl.toUpperCase()}
              </button>
            ))}
          </div>
          <button className="logout-btn" onClick={handleLogout}>Đăng xuất</button>
        </div>
      </div>

      {/* Main content area: chart + watchlist */}
      <div className="app-content">
        <div className="chart-container">
          <CandlestickChart symbol={selectedSymbol} intervalSeconds={labelToSeconds(intervalLabel)} />
        </div>
        <Watchlist
          onSymbolSelect={setSelectedSymbol}
          selectedSymbol={selectedSymbol}
        />
      </div>
    </div>
  );
};
