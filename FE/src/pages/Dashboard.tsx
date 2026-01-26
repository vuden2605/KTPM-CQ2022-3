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
      const API_BASE = (import.meta.env.VITE_API_BASE as string) || 'http://localhost:80';
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

  // Metrics state lifted from CandlestickChart
  const [metrics, setMetrics] = useState({ messagesPerSec: 0, bufferSize: 0, dropped: 0, fps: 0 });

  return (
    <div className="app">
      {/* Full-width header */}
      <div className="app-header">
        <div className="header-left">
          <div className="app-logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#2962ff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M2 17L12 22L22 17" stroke="#2962ff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M2 12L12 17L22 12" stroke="#2962ff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>TradeScope</span>
          </div>
        </div>
        <div className="header-right">
          <button className="logout-btn" onClick={handleLogout}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ marginRight: 6 }}>
              <path d="M17 16L21 12M21 12L17 8M21 12L7 12M13 16V17C13 18.6569 11.6569 20 10 20H6C4.34315 20 3 18.6569 3 17V7C3 5.34315 4.34315 4 6 4H10C11.6569 4 13 5.34315 13 7V8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Đăng xuất
          </button>
        </div>
      </div>

      {/* Main content area: chart + watchlist */}
      <div className="app-content">
        <div className="chart-container">
          {/* Chart Toolbar */}
          <div className="chart-toolbar" style={{ justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div className="symbol-info">
                <span className="symbol-name" style={{ fontWeight: 700, fontSize: 16 }}>{selectedSymbol}</span>
                <span className="connection-status" title="Connected via WebSocket" style={{ color: '#26a69a', fontSize: 12 }}>●</span>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div className="interval-selector">
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
            </div>
          </div>

          <CandlestickChart
            symbol={selectedSymbol}
            intervalSeconds={labelToSeconds(intervalLabel)}
            onMetricsUpdate={setMetrics}
          />
        </div>
        <Watchlist
          onSymbolSelect={setSelectedSymbol}
          selectedSymbol={selectedSymbol}
          metrics={metrics}
        />
      </div>
    </div>
  );
};
