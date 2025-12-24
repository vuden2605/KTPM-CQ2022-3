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
  const [symbols] = useState<Symbol[]>([
    { code: 'NDQ', name: 'NASDAQ', price: 25587.83, change: 126.13, changePercent: 0.50, type: 'index' },
    { code: 'VIX', name: 'VIX', price: 14.01, change: -0.08, changePercent: -0.57, type: 'index' },
    { code: 'BTCUSD', name: 'Bitcoin', price: 86790, change: -627, changePercent: -0.72, type: 'crypto' },
    { code: 'BTCUSDT', name: 'Bitcoin USDT', price: 86873.13, change: -612.87, changePercent: -0.70, type: 'crypto' },
    { code: 'ETHUSD', name: 'Ethereum', price: 2925.2, change: -37.6, changePercent: -1.27, type: 'crypto' },
    { code: 'HPG', name: 'Hòa Phát', price: 26650, change: -100, changePercent: -0.37, type: 'stock' },
    { code: 'VCB', name: 'Vietcombank', price: 56900, change: -300, changePercent: -0.52, type: 'stock' },
  ]);

  const getSymbolIcon = (type: string) => {
    switch (type) {
      case 'crypto':
        return '₿';
      case 'index':
        return '📊';
      default:
        return '🏢';
    }
  };

  return (
    <div className="watchlist">
      <div className="watchlist-header">
        <h3>Danh sách theo dõi</h3>
        <button className="add-btn">+</button>
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
