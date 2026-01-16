import { useState } from 'react';
import { CandlestickChart } from './components/CandlestickChart';
import { Watchlist } from './components/Watchlist';
import './App.css';

function App() {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [intervalLabel, setIntervalLabel] = useState('1m');

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
      <div className="chart-container">
        <div className="chart-header">
          <h2>{selectedSymbol}</h2>
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
        </div>
        <CandlestickChart symbol={selectedSymbol} intervalSeconds={labelToSeconds(intervalLabel)} />
      </div>
      <Watchlist
        onSymbolSelect={setSelectedSymbol}
        selectedSymbol={selectedSymbol}
      />
    </div>
  );
}

export default App;
