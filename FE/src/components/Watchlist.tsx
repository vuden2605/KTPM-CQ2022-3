import React, { useState, useEffect, useRef, useCallback } from 'react';
import { priceStore } from '../lib/priceStore';
import { MetricsPanel } from './MetricsPanel';
import '../styles/Watchlist.css';
import { getCryptoIcon } from './CryptoIcons';
import { AddSymbolModal } from './AddSymbolModal';

interface WatchSymbol {
  code: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume?: number;
  openPrice?: number;
  type: 'stock' | 'crypto' | 'index';
}

interface WatchlistProps {
  onSymbolSelect: (symbol: string) => void;
  selectedSymbol: string;
  metrics?: {
    messagesPerSec: number;
    bufferSize: number;
    dropped: number;
    fps: number;
  };
}

interface ViewSettings {
  tableView: boolean;
  columns: {
    price: boolean;
    change: boolean;
    changePercent: boolean;
    volume: boolean;
  };
  symbolDisplay: {
    logo: boolean;
    ticker: boolean;
    description: boolean;
  };
}

const DEFAULT_VIEW_SETTINGS: ViewSettings = {
  tableView: true,
  columns: {
    price: true,
    change: true,
    changePercent: true,
    volume: true,
  },
  symbolDisplay: {
    logo: true,
    ticker: true,
    description: true,
  },
};

const INITIAL_SYMBOLS: WatchSymbol[] = [
  { code: 'BTCUSDT', name: 'Bitcoin / USDT', price: 0, change: 0, changePercent: 0, volume: 0, type: 'crypto' },
  { code: 'BTCUSD', name: 'Bitcoin / USD', price: 0, change: 0, changePercent: 0, volume: 0, type: 'crypto' },
  { code: 'ETHUSDT', name: 'Ethereum / USDT', price: 0, change: 0, changePercent: 0, volume: 0, type: 'crypto' },
  { code: 'BNBUSDT', name: 'BNB / USDT', price: 0, change: 0, changePercent: 0, volume: 0, type: 'crypto' },
  { code: 'XRPUSDT', name: 'XRP / USDT', price: 0, change: 0, changePercent: 0, volume: 0, type: 'crypto' },
];

export const Watchlist = ({ onSymbolSelect, selectedSymbol, metrics }: WatchlistProps) => {
  const [symbols, setSymbols] = useState<WatchSymbol[]>(INITIAL_SYMBOLS);
  const [width, setWidth] = useState(() => {
    const saved = localStorage.getItem('watchlistWidth');
    return saved ? parseInt(saved, 10) : 350;
  });
  const [viewSettings, setViewSettings] = useState<ViewSettings>(() => {
    const saved = localStorage.getItem('watchlistViewSettings');
    return saved ? JSON.parse(saved) : DEFAULT_VIEW_SETTINGS;
  });
  const [menuOpen, setMenuOpen] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // Save width to localStorage
  useEffect(() => {
    localStorage.setItem('watchlistWidth', width.toString());
  }, [width]);

  // Save view settings to localStorage
  useEffect(() => {
    localStorage.setItem('watchlistViewSettings', JSON.stringify(viewSettings));
  }, [viewSettings]);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    if (menuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [menuOpen]);

  // Subscribe to priceStore for real-time price updates (centralized WebSocket data)
  useEffect(() => {
    // Subscribe all symbols to priceStore (it handles deduplication internally)
    const symbolCodes = symbols.map((s) => s.code);
    priceStore.subscribeAll(symbolCodes);

    // Listen for price updates
    const unsubscribe = priceStore.addListener((prices) => {
      setSymbols((prev) =>
        prev.map((s) => {
          const priceData = prices.get(s.code);
          if (priceData) {
            return {
              ...s,
              price: priceData.price,
              change: priceData.change,
              changePercent: priceData.changePercent,
              volume: priceData.volume24h,      // Use 24h volume from 1d candle
              openPrice: priceData.dailyOpen,   // Use daily open for reference
            };
          }
          return s;
        })
      );
    });

    return () => {
      unsubscribe();
    };
  }, []); // Only run once on mount

  // Resize functionality
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);

    const startX = e.clientX;
    const startWidth = width;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const deltaX = startX - moveEvent.clientX;
      const newWidth = Math.min(Math.max(startWidth + deltaX, 250), 800);
      setWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [width]);

  const getSymbolIcon = (code: string) => {
    return getCryptoIcon(code, 24);
  };

  const formatPrice = (price: number, code: string) => {
    if (price === 0) return '—';
    if (code.includes('XRP') || price < 1) {
      return price.toFixed(4);
    }
    return price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const formatVolume = (volume: number | undefined) => {
    if (!volume || volume === 0) return '—';
    if (volume >= 1e9) return (volume / 1e9).toFixed(4) + 'B';
    if (volume >= 1e6) return (volume / 1e6).toFixed(4) + 'M';
    if (volume >= 1e3) return (volume / 1e3).toFixed(4) + 'K';
    return volume.toFixed(4);
  };

  const toggleViewSetting = (category: keyof ViewSettings, key?: string) => {
    setViewSettings((prev) => {
      if (key && category !== 'tableView') {
        return {
          ...prev,
          [category]: {
            ...(prev[category] as object),
            [key]: !(prev[category] as any)[key],
          },
        };
      }
      if (category === 'tableView') {
        return { ...prev, tableView: !prev.tableView };
      }
      return prev;
    });
  };

  const handleToggleSymbol = (symbolCode: string) => {
    setSymbols(prev => {
      const exists = prev.find(s => s.code === symbolCode);
      if (exists) {
        // Remove
        return prev.filter(s => s.code !== symbolCode);
      } else {
        // Add
        const newSymbol: WatchSymbol = {
          code: symbolCode,
          name: `${symbolCode.replace('USDT', '')} / USDT`,
          price: 0,
          change: 0,
          changePercent: 0,
          volume: 0,
          type: 'crypto'
        };
        // Subscribe
        priceStore.subscribe(symbolCode);
        return [...prev, newSymbol];
      }
    });
  };

  return (
    <div
      ref={containerRef}
      className={`watchlist ${viewSettings.tableView ? 'table-view' : 'compact-view'}`}
      style={{ width }}
    >
      {/* Resize Handle */}
      <div
        className={`resize-handle ${isResizing ? 'dragging' : ''}`}
        onMouseDown={handleMouseDown}
      />

      {/* Header */}
      <div className="watchlist-header">
        <h3>Danh sách theo dõi (Crypto)</h3>
        <div className="header-actions">
          <button
            className="add-symbol-btn"
            onClick={() => setIsAddModalOpen(true)}
            title="Thêm mã"
          >
            +
          </button>
          <div className="menu-container" ref={menuRef}>
            <button
              className="menu-btn"
              onClick={() => setMenuOpen(!menuOpen)}
              title="Tùy chỉnh"
            >
              ⋯
            </button>
            {menuOpen && (
              <div className="menu-dropdown">
                {/* Table View Toggle */}
                <div className="menu-section">
                  <label className="menu-toggle">
                    <span>Chế độ xem dạng bảng</span>
                    <input
                      type="checkbox"
                      checked={viewSettings.tableView}
                      onChange={() => toggleViewSetting('tableView')}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>

                <div className="menu-divider"></div>

                {/* Column Visibility */}
                <div className="menu-section">
                  <div className="menu-section-title">TÙY CHỈNH CỘT</div>
                  {Object.entries(viewSettings.columns).map(([key, value]) => (
                    <label className="menu-checkbox" key={key}>
                      <input
                        type="checkbox"
                        checked={value}
                        onChange={() => toggleViewSetting('columns', key)}
                      />
                      <span className="checkmark"></span>
                      <span>
                        {key === 'price' && 'Lần cuối'}
                        {key === 'change' && 'Thay đổi giá'}
                        {key === 'changePercent' && '% Thay đổi'}
                        {key === 'volume' && 'Khối lượng'}
                      </span>
                    </label>
                  ))}
                </div>

                <div className="menu-divider"></div>

                {/* Symbol Display */}
                <div className="menu-section">
                  <div className="menu-section-title">HIỂN THỊ MÃ GIAO DỊCH</div>
                  {Object.entries(viewSettings.symbolDisplay).map(([key, value]) => (
                    <label className="menu-checkbox" key={key}>
                      <input
                        type="checkbox"
                        checked={value}
                        onChange={() => toggleViewSetting('symbolDisplay', key)}
                      />
                      <span className="checkmark"></span>
                      <span>
                        {key === 'logo' && 'Logo'}
                        {key === 'ticker' && 'Ticker'}
                        {key === 'description' && 'Mô tả'}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Table Header (only in table view) */}
      {viewSettings.tableView && (
        <div className="table-header">
          <div className="th-symbol">Mã</div>
          {viewSettings.columns.price && <div className="th-price">Lần cuối</div>}
          {viewSettings.columns.change && <div className="th-change">Thay đổi</div>}
          {viewSettings.columns.changePercent && <div className="th-percent">%Thay đổi</div>}
          {viewSettings.columns.volume && <div className="th-volume">Khối lượng</div>}
        </div>
      )}

      {/* Watchlist Items */}
      <div className="watchlist-items">
        {symbols.map((symbol) => (
          <div
            key={symbol.code}
            className={`watchlist-item ${selectedSymbol === symbol.code ? 'selected' : ''}`}
            onClick={() => onSymbolSelect(symbol.code)}
          >
            {viewSettings.tableView ? (
              // Table View Row
              <>
                <div className="cell-symbol">
                  {viewSettings.symbolDisplay.logo && (
                    <span className="symbol-icon">{getSymbolIcon(symbol.code)}</span>
                  )}
                  <div className="symbol-text">
                    {viewSettings.symbolDisplay.ticker && (
                      <div className="symbol-code">{symbol.code}</div>
                    )}
                    {viewSettings.symbolDisplay.description && (
                      <div className="symbol-name">{symbol.name}</div>
                    )}
                  </div>
                </div>
                <div className={`cell-price ${symbol.change >= 0 ? 'positive' : 'negative'}`}>
                  {formatPrice(symbol.price, symbol.code)}
                </div>
                {viewSettings.columns.change && (
                  <div className={`cell-change ${symbol.change >= 0 ? 'positive' : 'negative'}`}>
                    {symbol.price > 0 ? (symbol.change >= 0 ? '+' : '') + symbol.change.toFixed(4) : '—'}
                  </div>
                )}
                {viewSettings.columns.changePercent && (
                  <div className={`cell-percent ${symbol.changePercent >= 0 ? 'positive' : 'negative'}`}>
                    {symbol.price > 0 ? (symbol.changePercent >= 0 ? '+' : '') + symbol.changePercent.toFixed(4) + '%' : '—'}
                  </div>
                )}
                {viewSettings.columns.volume && (
                  <div className="cell-volume">{formatVolume(symbol.volume)}</div>
                )}
              </>
            ) : (
              // Compact View
              <>
                <div className="symbol-info">
                  {viewSettings.symbolDisplay.logo && (
                    <span className="symbol-icon">{getSymbolIcon(symbol.code)}</span>
                  )}
                  <div className="symbol-details">
                    {viewSettings.symbolDisplay.ticker && (
                      <div className="symbol-code">{symbol.code}</div>
                    )}
                    {viewSettings.symbolDisplay.description && (
                      <div className="symbol-name">{symbol.name}</div>
                    )}
                  </div>
                </div>
                <div className="symbol-price">
                  {viewSettings.columns.price && (
                    <div className="price">{formatPrice(symbol.price, symbol.code)}</div>
                  )}
                  {(viewSettings.columns.change || viewSettings.columns.changePercent) && (
                    <div className={`change ${symbol.change >= 0 ? 'positive' : 'negative'}`}>
                      {viewSettings.columns.change && symbol.price > 0 && (
                        <span>{symbol.change >= 0 ? '+' : ''}{symbol.change.toFixed(4)}</span>
                      )}
                      {viewSettings.columns.change && viewSettings.columns.changePercent && ' '}
                      {viewSettings.columns.changePercent && symbol.price > 0 && (
                        <span>({symbol.changePercent.toFixed(4)}%)</span>
                      )}
                      {symbol.price === 0 && '—'}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        ))}
      </div>

      {metrics && (
        <div className="watchlist-footer">
          <MetricsPanel {...metrics} />
        </div>
      )}


      <AddSymbolModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSelect={handleToggleSymbol}
        existingSymbols={symbols.map(s => s.code)}
      />
    </div>
  );
};
