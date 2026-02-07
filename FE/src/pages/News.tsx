import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../App.css';

interface NewsInfo {
  news_id: string;
  timestamp: string;
  title: string;
  content?: string;
  author?: string; // Added author field
  sentiment_score: number;
  is_breaking: boolean;
}

interface NewsListResponse {
  symbol: string;
  hours: number;
  total_news: number;
  news_list: NewsInfo[];
  timestamp: string;
}

export const News = () => {
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
    window.addEventListener('storage', loadSymbols);
    return () => window.removeEventListener('storage', loadSymbols);
  }, []);

  // Filter State
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [hours, setHours] = useState(24);
  const [newsList, setNewsList] = useState<NewsInfo[]>([]);
  const [selectedNews, setSelectedNews] = useState<NewsInfo | null>(null);

  // UI State
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize from URL params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlSymbol = params.get('symbol');

    if (urlSymbol) {
      setSymbol(urlSymbol);
    }
    // We can't set selectedNews here directly because we haven't fetched the list yet.
    // We will handle specific news selection in the fetch effect or after data load.
  }, []);

  // Default symbol fallback
  useEffect(() => {
    // Only if not URL param initialized (simple check: if symbol is empty? but default is BTCUSDT)
    // Actually, availableSymbols logic might override if we are not careful.
    // Let's rely on the URL param effect running once. 
    // If symbol is valid in availableSymbols, it stays. If not, fallback?
    // For now, let's just ensure if URL param set it, we respect it.
    if (availableSymbols.length > 0 && !availableSymbols.find(s => s.code === symbol) && symbol !== 'ALL') {
      // Check if it's a valid symbol at all? 
      // If the user navigates with ?symbol=XYZ and XYZ is not in watchlist, 
      // do we want to force it? Maybe yes.
      // So let's only fallback if the CURRENT symbol is totally invalid AND not from URL (hard to track source).
      // Simplified: If symbol is "BTCUSDT" (default) but watchlist doesn't have it? Unlikely.
      const params = new URLSearchParams(window.location.search);
      if (!params.get('symbol')) {
        setSymbol('ALL'); // Default to ALL if current symbol invalid in context
      }
    } else if (availableSymbols.length === 0 && symbol !== 'ALL') {
      // Safety: If no symbols, default to ALL (or maybe we should just allow custom input?)
      // But for now, ALL is safe.
      setSymbol('ALL');
    }
  }, [availableSymbols]);

  const fetchNews = async () => {
    setLoading(true);
    setError(null);

    try {
      const API_BASE = (import.meta.env.VITE_API_BASE as string) || 'http://localhost:80';
      const response = await fetch(`${API_BASE}/api/ai/news?symbol=${symbol}&hours=${hours}`);

      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }

      const data: NewsListResponse = await response.json();
      setNewsList(data.news_list || []);

      // Auto-select logic
      const params = new URLSearchParams(window.location.search);
      const urlNewsId = params.get('newsId');

      let found = null;
      if (urlNewsId && data.news_list) {
        found = data.news_list.find(n => n.news_id === urlNewsId || n.news_id === decodeURIComponent(urlNewsId));
      }

      if (found) {
        setSelectedNews(found);
        // Optional: Scroll into view logic could be added here
      } else if (data.news_list && data.news_list.length > 0 && !selectedNews) {
        setSelectedNews(data.news_list[0]);
      } else if (data.news_list.length === 0) {
        setSelectedNews(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch news');
      setNewsList([]);
    } finally {
      setLoading(false);
    }
  };

  // Auto fetch when filters change
  useEffect(() => {
    fetchNews();
  }, [symbol, hours]);

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
            <span>TradeScope News</span>
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
            navigate('/login');
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ marginRight: 6 }}>
              <path d="M17 16L21 12M21 12L17 8M21 12L7 12M13 16V17C13 18.6569 11.6569 20 10 20H6C4.34315 20 3 18.6569 3 17V7C3 5.34315 4.34315 4 6 4H10C11.6569 4 13 5.34315 13 7V8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="app-content" style={{ flexDirection: 'column', padding: '20px', height: 'calc(100vh - 60px)', overflow: 'hidden' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>

          {/* Filters */}
          <div style={{
            display: 'flex',
            gap: '16px',
            marginBottom: '16px',
            flexShrink: 0,
            alignItems: 'center'
          }}>
            <div style={{ minWidth: '200px' }}>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: '4px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-panel)',
                  color: 'var(--text-primary)'
                }}
              >
                <option value="ALL">All Followed Symbols</option>
                {availableSymbols.length > 0 ? availableSymbols.map(s => (
                  <option key={s.code} value={s.code}>{s.code}</option>
                )) : <option disabled>No symbols in watchlist</option>}
              </select>
            </div>
            <div style={{ minWidth: '150px' }}>
              <select
                value={hours}
                onChange={(e) => setHours(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: '4px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-panel)',
                  color: 'var(--text-primary)'
                }}
              >
                <option value={6}>Last 6 Hours</option>
                <option value={12}>Last 12 Hours</option>
                <option value={24}>Last 24 Hours</option>
                <option value={48}>Last 48 Hours</option>
                <option value={168}>Last 7 Days</option>
              </select>
            </div>
            <button
              onClick={fetchNews}
              disabled={loading}
              style={{
                padding: '8px 16px',
                background: loading ? 'var(--text-secondary)' : '#2962ff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>

          {error && (
            <div style={{
              padding: '12px',
              background: 'rgba(231, 76, 60, 0.1)',
              border: '1px solid #e74c3c',
              color: '#e74c3c',
              borderRadius: '4px',
              marginBottom: '16px'
            }}>
              {error}
            </div>
          )}

          {/* Content Area (2 Panic Layout) */}
          <div style={{ display: 'flex', gap: '20px', flex: 1, minHeight: 0 }}>

            {/* Left Pane: News List */}
            <div style={{
              width: '400px',
              background: 'var(--bg-panel)',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              display: 'flex',
              flexDirection: 'column',
              flexShrink: 0
            }}>
              <div style={{ padding: '16px', borderBottom: '1px solid var(--border-color)', fontWeight: 600 }}>
                Latest News ({newsList.length})
              </div>
              <div style={{ overflowY: 'auto', flex: 1 }}>
                {newsList.length === 0 && !loading && (
                  <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                    No news found for this period.
                  </div>
                )}
                {newsList.map(item => (
                  <div
                    key={item.news_id}
                    onClick={() => setSelectedNews(item)}
                    style={{
                      padding: '16px',
                      borderBottom: '1px solid var(--border-color)',
                      cursor: 'pointer',
                      background: selectedNews?.news_id === item.news_id ? 'rgba(41, 98, 255, 0.1)' : 'transparent',
                      transition: 'background 0.2s'
                    }}
                  >
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                      <span>{new Date(item.timestamp).toLocaleString()}</span>
                      {item.is_breaking && (
                        <span style={{ color: '#e74c3c', fontWeight: 700 }}>BREAKING</span>
                      )}
                    </div>
                    <div style={{ fontWeight: 500, lineHeight: '1.4', marginBottom: '8px' }}>
                      {item.title}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{
                        width: '8px', height: '8px', borderRadius: '50%',
                        background: item.sentiment_score > 0.6 ? '#26a69a' : (item.sentiment_score < 0.4 ? '#ef5350' : '#f1c40f')
                      }} />
                      <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        Sentiment: {item.sentiment_score.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Pane: Content Reading */}
            <div style={{
              flex: 1,
              background: 'var(--bg-panel)',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}>
              {selectedNews ? (
                <div style={{ padding: '30px', overflowY: 'auto', height: '100%' }}>
                  <div style={{
                    fontSize: '24px',
                    fontWeight: 700,
                    marginBottom: '16px',
                    lineHeight: '1.3'
                  }}>
                    {selectedNews.title}
                  </div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '16px',
                    marginBottom: '24px',
                    color: 'var(--text-secondary)',
                    fontSize: '14px',
                    borderBottom: '1px solid var(--border-color)',
                    paddingBottom: '16px'
                  }}>
                    <span>{new Date(selectedNews.timestamp).toLocaleString()}</span>
                    <span>|</span>
                    <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                      {selectedNews.author && selectedNews.author !== 'Unknown' ? selectedNews.author : 'Unknown Author'}
                    </span>
                    <span>|</span>
                    <span style={{
                      color: selectedNews.sentiment_score > 0.6 ? '#26a69a' : (selectedNews.sentiment_score < 0.4 ? '#ef5350' : '#f1c40f'),
                      fontWeight: 600
                    }}>
                      Sentiment Score: {selectedNews.sentiment_score.toFixed(2)}
                    </span>
                  </div>

                  <div style={{
                    fontSize: '16px',
                    lineHeight: '1.8',
                    color: 'var(--text-primary)',
                    whiteSpace: 'pre-line' // Preserve line breaks from backend
                  }}>
                    {selectedNews.content || (
                      <span style={{ fontStyle: 'italic', color: 'var(--text-secondary)' }}>
                        Content not available for this article.
                      </span>
                    )}
                  </div>
                </div>
              ) : (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  color: 'var(--text-secondary)',
                  flexDirection: 'column',
                  gap: '16px'
                }}>
                  <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ opacity: 0.3 }}>
                    <path d="M19 20H5C3.89543 20 3 19.1046 3 18V6C3 4.89543 3.89543 4 5 4H19C20.1046 4 21 4.89543 21 6V18C21 19.1046 20.1046 20 19 20Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M17 9H7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M17 13H7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M13 17H7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <div>Select a news item to read content</div>
                </div>
              )}
            </div>

          </div>
        </div>
      </div>
    </div >
  );
};
