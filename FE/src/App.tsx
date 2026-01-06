import { useState } from 'react';
import { CandlestickChart } from './components/CandlestickChart';
import { Watchlist } from './components/Watchlist';
import './App.css';

function App() {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');

  return (
    <div className="app">
      <div className="chart-container">
        <div className="chart-header">
          <h2>{selectedSymbol}</h2>
          <div className="chart-controls">
            <button className="interval-btn active">1D</button>
            <button className="interval-btn">1W</button>
            <button className="interval-btn">1M</button>
            <button className="interval-btn">3M</button>
            <button className="interval-btn">1Y</button>
          </div>
        </div>
        <CandlestickChart symbol={selectedSymbol} />
      </div>
      <Watchlist
        onSymbolSelect={setSelectedSymbol}
        selectedSymbol={selectedSymbol}
      />
    </div>
  );
}

export default App;
