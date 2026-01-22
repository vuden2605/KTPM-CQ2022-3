// Shared price store - singleton that manages real-time price data for all symbols
// This centralizes WebSocket subscriptions to avoid duplicates
// Uses ROLLING 24H calculation: currentPrice - price24hAgo (like Binance/TradingView)

import { sharedWs } from './sharedWs';

export interface SymbolPrice {
  symbol: string;
  price: number;
  price24hAgo: number;   // Price 24 hours ago (for rolling 24h change)
  high: number;
  low: number;
  close: number;
  change: number;        // price - price24hAgo (rolling 24h change)
  changePercent: number; // (change / price24hAgo) * 100
  volume24h: number;     // 24h volume from 1d candle
  lastUpdate: number;
}

type PriceListener = (prices: Map<string, SymbolPrice>) => void;

const API_BASE = 'http://localhost:8082/api/v1';

class PriceStore {
  private prices: Map<string, SymbolPrice> = new Map();
  private listeners: Set<PriceListener> = new Set();
  private subscriptions: Map<string, () => void> = new Map();
  private price24hAgo: Map<string, number> = new Map();
  private dailyVolumes: Map<string, number> = new Map();
  private initialized: Set<string> = new Set();

  // Fetch price 24 hours ago by getting recent candles with 1h interval
  private async fetchPrice24hAgo(symbol: string): Promise<number | null> {
    try {
      const token = localStorage.getItem('accessToken');
      // Use /candles/recent endpoint with 1h interval to get hourly candles
      const response = await fetch(`${API_BASE}/candles/recent?symbol=${symbol}&interval=1h`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });

      if (!response.ok) {
        console.warn(`Failed to fetch hourly candles for ${symbol}:`, response.status);
        return null;
      }

      const result = await response.json();
      // API returns { data: [...], message: "..." } format
      const data = result.data || result;

      if (Array.isArray(data) && data.length > 0) {
        // Sort by time ascending if not already
        const sorted = [...data].sort((a, b) => Number(a.openTime || a.time) - Number(b.openTime || b.time));
        // Get the oldest candle's close price (approximately 24h ago)
        const oldestCandle = sorted[0];
        const price = Number(oldestCandle.close);
        return price;
      }
      return null;
    } catch (e) {
      console.error(`Error fetching hourly candles for ${symbol}:`, e);
      return null;
    }
  }

  // Fetch 24h volume from daily candle
  private async fetchDailyVolume(symbol: string): Promise<number | null> {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${API_BASE}/candles/latest-candle?interval=1d`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });

      if (!response.ok) {
        return null;
      }

      const data = await response.json();
      const candle = Array.isArray(data)
        ? data.find((c: any) => c.symbol === symbol)
        : data.symbol === symbol ? data : null;

      if (candle) {
        return Number(candle.volume);
      }
      return null;
    } catch (e) {
      console.error(`Error fetching daily candle for ${symbol}:`, e);
      return null;
    }
  }

  // Subscribe to a symbol's price updates
  async subscribe(symbol: string) {
    // Check if already subscribed
    const key1m = `${symbol}:1m`;
    const key1d = `${symbol}:1d`;

    if (this.subscriptions.has(key1m)) {
      return; // Already subscribed
    }

    // Fetch initial data: price 24h ago and 24h volume
    if (!this.initialized.has(symbol)) {
      const [price24h, volume24h] = await Promise.all([
        this.fetchPrice24hAgo(symbol),
        this.fetchDailyVolume(symbol),
      ]);

      if (price24h !== null) {
        this.price24hAgo.set(symbol, price24h);
      }
      if (volume24h !== null) {
        this.dailyVolumes.set(symbol, volume24h);
      }

      this.initialized.add(symbol);
    }

    // Handler for 1m candles (current price updates)
    const handler1m = (candle: any) => {
      const closePrice = Number(candle.close);
      const price24hAgo = this.price24hAgo.get(symbol) || closePrice;
      const volume24h = this.dailyVolumes.get(symbol) || 0;

      // Rolling 24h change calculation
      const change = closePrice - price24hAgo;
      const changePercent = price24hAgo > 0 ? (change / price24hAgo) * 100 : 0;

      const priceData: SymbolPrice = {
        symbol,
        price: closePrice,
        price24hAgo,
        high: Number(candle.high),
        low: Number(candle.low),
        close: closePrice,
        change,
        changePercent,
        volume24h,
        lastUpdate: Date.now(),
      };

      this.prices.set(symbol, priceData);
      this.notifyListeners();
    };

    // Handler for 1d candles (volume updates)
    const handler1d = (candle: any) => {
      const volume = Number(candle.volume) || 0;
      this.dailyVolumes.set(symbol, volume);

      // Update price data with new volume
      const existing = this.prices.get(symbol);
      if (existing) {
        existing.volume24h = volume;
        this.prices.set(symbol, existing);
        this.notifyListeners();
      }
    };

    // Subscribe to both 1m and 1d
    const unsub1m = sharedWs.subscribe(symbol, handler1m, '1m');
    const unsub1d = sharedWs.subscribe(symbol, handler1d, '1d');

    this.subscriptions.set(key1m, unsub1m);
    this.subscriptions.set(key1d, unsub1d);
  }

  // Unsubscribe from a symbol
  unsubscribe(symbol: string) {
    const key1m = `${symbol}:1m`;
    const key1d = `${symbol}:1d`;

    const unsub1m = this.subscriptions.get(key1m);
    const unsub1d = this.subscriptions.get(key1d);

    if (unsub1m) {
      unsub1m();
      this.subscriptions.delete(key1m);
    }
    if (unsub1d) {
      unsub1d();
      this.subscriptions.delete(key1d);
    }
  }

  // Subscribe multiple symbols at once
  async subscribeAll(symbols: string[]) {
    await Promise.all(symbols.map((sym) => this.subscribe(sym)));
  }

  // Add a listener for price changes
  addListener(listener: PriceListener): () => void {
    this.listeners.add(listener);
    // Immediately notify with current data
    listener(this.prices);
    return () => this.listeners.delete(listener);
  }

  // Get current price for a symbol
  getPrice(symbol: string): SymbolPrice | undefined {
    return this.prices.get(symbol);
  }

  // Get all prices
  getAllPrices(): Map<string, SymbolPrice> {
    return new Map(this.prices);
  }

  private notifyListeners() {
    const pricesCopy = new Map(this.prices);
    this.listeners.forEach((listener) => {
      try {
        listener(pricesCopy);
      } catch (e) {
        console.error('Price listener error:', e);
      }
    });
  }

  // Refresh 24h ago prices (call periodically to keep rolling window accurate)
  async refresh24hPrices() {
    const symbols = Array.from(this.initialized);
    for (const symbol of symbols) {
      const price24h = await this.fetchPrice24hAgo(symbol);
      if (price24h !== null) {
        this.price24hAgo.set(symbol, price24h);
      }
    }
  }
}

// Singleton instance
export const priceStore = new PriceStore();
