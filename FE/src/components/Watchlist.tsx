import { useState } from 'react';
import './Watchlist.css';

interface Symbol {
  code: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  type: 'stock' | 'crypto' | 'index';
}

interface WatchlistProps {
  onSymbolSelect: (symbol: string) => void;
  selectedSymbol: string;
}

export const Watchlist = ({ onSymbolSelect, selectedSymbol }: WatchlistProps) => {
  // Only show cryptocurrency pairs supported by the backend ingest-service
  const [symbols] = useState<Symbol[]>([
    { code: 'BTCUSDT', name: 'Bitcoin / USDT', price: 86873.13, change: -612.87, changePercent: -0.70, type: 'crypto' },
    { code: 'ETHUSDT', name: 'Ethereum / USDT', price: 2925.2, change: -37.6, changePercent: -1.27, type: 'crypto' },
    { code: 'BNBUSDT', name: 'BNB / USDT', price: 320.5, change: 2.1, changePercent: 0.66, type: 'crypto' },
    { code: 'XRPUSDT', name: 'XRP / USDT', price: 0.62, change: -0.01, changePercent: -1.59, type: 'crypto' },
    { code: 'ADAUSDT', name: 'ADA / USDT', price: 0.42, change: 0.005, changePercent: 1.20, type: 'crypto' },
  ]);

  const getSymbolIcon = (type: string) => {
    return '₿';
  };

  return (
    <div className="watchlist">
      <div className="watchlist-header">
        <h3>Danh sách theo dõi (Crypto)</h3>
      </div>

      <div className="watchlist-items">
        {symbols.map((symbol) => (
          <div
            key={symbol.code}
            className={`watchlist-item ${selectedSymbol === symbol.code ? 'selected' : ''}`}
            onClick={() => onSymbolSelect(symbol.code)}
          >
            <div className="symbol-info">
              <span className="symbol-icon">{getSymbolIcon(symbol.type)}</span>
              <div className="symbol-details">
                <div className="symbol-code">{symbol.code}</div>
                <div className="symbol-name">{symbol.name}</div>
              </div>
            </div>
            <div className="symbol-price">
              <div className="price">{symbol.price.toLocaleString()}</div>
              <div className={`change ${symbol.change >= 0 ? 'positive' : 'negative'}`}>
                {symbol.change >= 0 ? '+' : ''}{symbol.change.toFixed(2)} ({symbol.changePercent.toFixed(2)}%)
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="symbol-detail">
        <h4>{selectedSymbol}</h4>
        <div className="detail-row">
          <span className="label">Giá</span>
          <span className="value">
            {symbols.find(s => s.code === selectedSymbol)?.price.toLocaleString() || 'N/A'}
          </span>
        </div>
        <div className="detail-row">
          <span className="label">Thay đổi</span>
          <span className={`value ${(symbols.find(s => s.code === selectedSymbol)?.change || 0) >= 0 ? 'positive' : 'negative'}`}>
            {symbols.find(s => s.code === selectedSymbol)?.change.toFixed(2) || 'N/A'}
          </span>
        </div>
      </div>
    </div>
  );
};
