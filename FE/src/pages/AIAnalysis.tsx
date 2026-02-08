import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../App.css';

interface NewsInfo {
  news_id: string;
  timestamp: string;
  title: string;
  sentiment_score: number;
  is_breaking: boolean;
}

interface PredictResponse {
  symbol: string;
  horizon: string;
  final_prediction: string;
  final_confidence: number;
  total_news_analyzed: number;
  explanation: string;
  top_news: NewsInfo[];
  timestamp: string;
}

export const AIAnalysis = () => {
  const navigate = useNavigate();

  // Load symbols from localStorage
  const [availableSymbols, setAvailableSymbols] = useState<{ code: string, name: string }[]>([]);

  useEffect(() => {
    const loadSymbols = () => {
      const saved = localStorage.getItem('watchlistSymbols');
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed)) {
            setAvailableSymbols(parsed.map((s: any) => ({ code: s.code, name: s.name || s.code })));
          }
        } catch (e) {
          console.error("Failed to parse watchlist symbols", e);
        }
      }
    };

    loadSymbols();

    // Optional: Listen for storage changes if multiple tabs update it
    window.addEventListener('storage', loadSymbols);
    return () => window.removeEventListener('storage', loadSymbols);
  }, []);

  // Form State - Initialize from localStorage if available
  const [symbol, setSymbol] = useState(() => {
    const saved = localStorage.getItem('aiAnalysisState');
    return saved ? JSON.parse(saved).symbol : 'BTCUSDT';
  });
  const [horizon, setHorizon] = useState(() => {
    const saved = localStorage.getItem('aiAnalysisState');
    return saved ? JSON.parse(saved).horizon : '24h';
  });
  const [hours, setHours] = useState(() => {
    const saved = localStorage.getItem('aiAnalysisState');
    return saved ? JSON.parse(saved).hours : 6;
  });

  // UI State
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictResponse | null>(() => {
    const saved = localStorage.getItem('aiAnalysisState');
    return saved ? JSON.parse(saved).result : null;
  });

  // Persist state to localStorage whenever it changes
  useEffect(() => {
    const state = {
      symbol,
      horizon,
      hours,
      result
    };
    localStorage.setItem('aiAnalysisState', JSON.stringify(state));
  }, [symbol, horizon, hours, result]);

  // Update symbol if current selection is not in list (optional, but good UX to default to first available)
  useEffect(() => {
    // Only override if we don't have a valid symbol (and not loading from storage which might have a valid one not yet in list)
    // Actually, let's trust localStorage or default. The previous logic might override user's saved symbol 
    // if availableSymbols loads later. 
    // Better logic: If symbol is NOT in availableSymbols AND availableSymbols is loaded, defaulting might be needed.
    // But for now, let's keep it simple and trust persistence.
    if (availableSymbols.length > 0 && !availableSymbols.find(s => s.code === symbol)) {
      // If persisted symbol is invalid, reset to first available.
      // setSymbol(availableSymbols[0].code); 
      // Commented out to prevent overriding persisted valid symbol before list fully loads
    }
  }, [availableSymbols, symbol]);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const API_BASE = (import.meta.env.VITE_API_BASE as string) || 'http://localhost:80';
      const response = await fetch(`${API_BASE}/api/ai/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol,
          horizon,
          hours
        }),
      });

      if (!response.ok) {
        let errorMessage = `API Error: ${response.statusText}`;
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch (e) {
          // Ignore parsing error, use default message
        }

        // Customize message for 404 (No news found)
        if (response.status === 404) {
          if (errorMessage.includes("No news found")) {
            throw new Error(`No news found for ${symbol} in the last ${hours} hours. Please try increasing the search history or choose another symbol.`);
          }
        }

        throw new Error(errorMessage);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

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
            <span>TradeScope AI</span>
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

          <button
            className="news-btn"
            onClick={() => navigate('/news')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 12px',
              background: '#009688', // Teal color for News
              border: 'none',
              borderRadius: '4px',
              color: 'white',
              cursor: 'pointer'
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M19 20H5C3.89543 20 3 19.1046 3 18V6C3 4.89543 3.89543 4 5 4H19C20.1046 4 21 4.89543 21 6V18C21 19.1046 20.1046 20 19 20Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M17 9H7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M17 13H7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M13 17H7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Market News
          </button>

          <button className="logout-btn" onClick={() => {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('role');
            localStorage.removeItem('aiAnalysisState'); // Clear persisted state
            navigate('/login');
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ marginRight: 6 }}>
              <path d="M17 16L21 12M21 12L17 8M21 12L7 12M13 16V17C13 18.6569 11.6569 20 10 20H6C4.34315 20 3 18.6569 3 17V7C3 5.34315 4.34315 4 6 4H10C11.6569 4 13 5.34315 13 7V8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Logout
          </button>
        </div>
      </div>

      <div className="app-content" style={{ flexDirection: 'column', padding: '20px', overflowY: 'scroll' }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto', width: '100%' }}>

          <div style={{ marginBottom: '24px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>AI Market Analysis</h1>
            <p style={{ color: 'var(--text-secondary)' }}>Get AI-powered predictions based on real-time news sentiment and market data.</p>
          </div>

          <div style={{
            display: 'flex',
            gap: '24px',
            background: 'var(--bg-panel)',
            padding: '20px',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
            alignItems: 'flex-end',
            justifyContent: 'center',
            marginBottom: '24px'
          }}>
            <div style={{ width: '250px' }}>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)', fontSize: '13px' }}>Symbol</label>
              <div style={{ position: 'relative' }}>
                <select
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    paddingRight: '36px', // Make space for custom arrow
                    borderRadius: '4px',
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-app)',
                    color: 'var(--text-primary)',
                    appearance: 'none',
                    WebkitAppearance: 'none',
                    MozAppearance: 'none',
                    backgroundImage: `url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23888' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e")`,
                    backgroundRepeat: 'no-repeat',
                    backgroundPosition: 'right 16px center',
                    backgroundSize: '16px',
                    cursor: 'pointer'
                  }}
                >
                  {availableSymbols.length === 0 && <option value="BTCUSDT">BTCUSDT (Default)</option>}
                  {availableSymbols.map(s => (
                    <option key={s.code} value={s.code}>
                      {s.code}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div style={{ width: '180px' }}>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)', fontSize: '13px' }}>Horizon</label>
              <div style={{ position: 'relative' }}>
                <select
                  value={horizon}
                  onChange={(e) => setHorizon(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    paddingRight: '36px',
                    borderRadius: '4px',
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-app)',
                    color: 'var(--text-primary)',
                    appearance: 'none',
                    WebkitAppearance: 'none',
                    MozAppearance: 'none',
                    backgroundImage: `url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23888' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e")`,
                    backgroundRepeat: 'no-repeat',
                    backgroundPosition: 'right 16px center',
                    backgroundSize: '16px',
                    cursor: 'pointer'
                  }}
                >
                  <option value="1h">1 Hour</option>
                  <option value="24h">24 Hours</option>
                </select>
              </div>
            </div>
            <div style={{ width: '150px' }}>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)', fontSize: '13px' }}>History (Hours)</label>
              <input
                type="number"
                value={hours}
                onChange={(e) => setHours(Number(e.target.value))}
                min={1}
                max={48}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: '4px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-app)',
                  color: 'var(--text-primary)'
                }}
              />
            </div>
            <button
              onClick={handleAnalyze}
              disabled={loading}
              style={{
                width: '160px',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                background: loading ? 'var(--text-secondary)' : '#2962ff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontWeight: 600,
                height: '38px',
                flexShrink: 0
              }}
            >
              {loading ? 'Analyzing...' : 'Analyze Market'}
            </button>
          </div>

          {error && (
            <div style={{ padding: '12px', background: 'rgba(231, 76, 60, 0.1)', border: '1px solid #e74c3c', color: '#e74c3c', borderRadius: '4px', marginBottom: '24px' }}>
              {error}
            </div>
          )}

          {result && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {/* Summary Card */}
              <div style={{ background: 'var(--bg-panel)', borderRadius: '8px', border: '1px solid var(--border-color)', overflow: 'hidden' }}>
                <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Analysis Result for {result.symbol}</h3>
                  <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{new Date(result.timestamp).toLocaleString()}</span>
                </div>
                <div style={{ padding: '24px', display: 'flex', gap: '40px', alignItems: 'center' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '8px' }}>Prediction ({result.horizon})</div>
                    <div style={{
                      fontSize: '32px',
                      fontWeight: 800,
                      color: result.final_prediction === 'UP' ? '#26a69a' : '#ef5350'
                    }}>
                      {result.final_prediction}
                    </div>
                  </div>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Confidence Score</span>
                      <span style={{ fontSize: '14px', fontWeight: 600 }}>{(result.final_confidence * 100).toFixed(2)}%</span>
                    </div>
                    <div style={{ height: '8px', background: 'var(--bg-app)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%',
                        width: `${result.final_confidence * 100}%`,
                        background: result.final_prediction === 'UP' ? '#26a69a' : '#ef5350'
                      }} />
                    </div>
                  </div>

                  <div style={{ textAlign: 'center', paddingLeft: '40px', borderLeft: '1px solid var(--border-color)' }}>
                    <div style={{ fontSize: '24px', fontWeight: 700 }}>{result.total_news_analyzed}</div>
                    <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>News Analyzed</div>
                  </div>
                </div>
              </div>

              {/* Explanation */}
              <div style={{ background: 'var(--bg-panel)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: 600 }}>AI Explanation</h3>
                </div>
                <div style={{ padding: '20px', lineHeight: '1.6', fontSize: '15px' }}>
                  {result.explanation.split('\n').map((line, i) => (
                    <p key={i} style={{ marginBottom: line.trim() === '' ? '0' : '12px' }}>
                      {line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .split(/(<strong>.*?<\/strong>)/g)
                        .map((part, index) =>
                          part.startsWith('<strong>') ?
                            <strong key={index}>{part.replace(/<\/?strong>/g, '')}</strong> :
                            part
                        )}
                    </p>
                  ))}
                </div>
              </div>

              {/* News List */}
              <div style={{ background: 'var(--bg-panel)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Top Influential News</h3>
                </div>
                <div>
                  {result.top_news.map((news) => (
                    <div
                      key={news.news_id}
                      onClick={() => navigate(`/news?symbol=${symbol}&newsId=${news.news_id}`)}
                      style={{
                        padding: '16px 20px',
                        borderBottom: '1px solid var(--border-color)',
                        display: 'flex',
                        gap: '16px',
                        cursor: 'pointer',
                        transition: 'background 0.2s'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    >
                      <div style={{
                        width: '4px',
                        background: news.sentiment_score > 0.6 ? '#26a69a' : (news.sentiment_score < 0.4 ? '#ef5350' : '#f1c40f'),
                        borderRadius: '2px'
                      }} />
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '6px' }}>
                          {news.is_breaking && (
                            <span style={{ fontSize: '10px', background: '#e74c3c', color: 'white', padding: '2px 6px', borderRadius: '4px', fontWeight: 700 }}>BREAKING</span>
                          )}
                          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{new Date(news.timestamp).toLocaleString()}</span>
                          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>• Sentiment: {news.sentiment_score.toFixed(2)}</span>
                        </div>
                        <div style={{ fontSize: '15px', fontWeight: 500 }}>{news.title}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          )}

        </div>
      </div>
    </div>
  );
};
